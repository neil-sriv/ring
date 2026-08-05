"""Script to backfill search documents for all users, groups, letters, questions, and responses."""

from __future__ import annotations

from loguru import logger
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ring.api_identifier.api_identified_model import APIIdentified
from ring.scripts.dependencies import (
    ScriptDependencies,
    get_script_dependencies,
    script_depends,
)
from ring.search.crud.hybrid_search import (
    type_to_search_registration,
)
from ring.search.models.hybrid_search import (
    HybridSearchDocument,
    HybridSearchDocumentAssociation,
    SearchableType,
)


def get_batch_size(searchable_type: SearchableType) -> int:
    """Get batch size for a specific searchable type."""
    batch_sizes = {
        SearchableType.USER: 50,
        SearchableType.GROUP: 50,
        SearchableType.QUESTION: 25,
        SearchableType.LETTER: 10,
        SearchableType.RESPONSE: 10,
    }
    return batch_sizes.get(searchable_type, 20)


def run_script(
    searchable_types: list[SearchableType] | None = None,
    replace_existing: bool = False,
    dry_run: bool = True,
    batch_delay: float = 0.5,
    deps: ScriptDependencies = script_depends(get_script_dependencies),
) -> None:
    """Backfill search documents for specified types.

    When ``replace_existing`` is True, associations are recreated with filter and
    sort metadata (``group_api_id``, ``participant_api_id``, ``entity_created_at``)
    via each type's search registrar. Run with ``dry_run=False`` on production
    after deploying the search filter migration.

    Args:
        searchable_types (list[SearchableType] | None): Types to backfill. If None, backfills all types.
        replace_existing (bool): Whether to replace existing documents
        dry_run (bool): Whether to commit changes
        batch_delay (float): Delay between batches in seconds
        deps (ScriptDependencies): Script dependencies provided by script_depends
    """
    logger.info(
        "Backfilling search documents for all users, groups, letters, questions, and responses"
    )
    if searchable_types is None:
        searchable_types = [
            SearchableType.USER,
            SearchableType.GROUP,
            SearchableType.LETTER,
            SearchableType.QUESTION,
            SearchableType.RESPONSE,
        ]
    else:
        searchable_types = [
            SearchableType(searchable_type)
            for searchable_type in searchable_types
        ]

    for searchable_type in searchable_types:
        model_class = type_to_search_registration(searchable_type).model_class
        models = deps.db.scalars(select(model_class)).all()

        logger.info(
            f"Found {len(models)} {searchable_type.value} models to process"
        )

        if replace_existing:
            _truncate_search_documents(deps.db, searchable_type)
            _backfill_search_documents_batched(
                deps.db, searchable_type, models, batch_delay
            )
        else:
            _, models_without_documents = _partition_models_by_documents(
                deps.db, models
            )
            logger.info(
                f"Found {len(models_without_documents)} {searchable_type.value} models without search documents"
            )
            _backfill_search_documents_batched(
                deps.db, searchable_type, models_without_documents, batch_delay
            )

    if dry_run:
        logger.info("Dry run, rolling back")
        deps.db.rollback()
    else:
        deps.db.commit()


def _partition_models_by_documents(
    db: Session, models: list[APIIdentified]
) -> tuple[list[APIIdentified], list[APIIdentified]]:
    models_with_documents = []
    models_without_documents = []
    associations = db.scalars(
        select(HybridSearchDocumentAssociation).where(
            HybridSearchDocumentAssociation.model_api_identifier.in_(
                [model.api_identifier for model in models]
            )
        )
    ).all()
    for model in models:
        if model.api_identifier in [
            association.model_api_identifier for association in associations
        ]:
            models_with_documents.append(model)
        else:
            models_without_documents.append(model)
    return models_with_documents, models_without_documents


def _backfill_search_documents_batched(
    db: Session,
    searchable_type: SearchableType,
    models: list[APIIdentified],
    batch_delay: float,
) -> list[HybridSearchDocument]:
    """Backfill search documents using batched processing to avoid quota limits.

    Args:
        db: Database session
        searchable_type: Type of searchable content
        models: List of models to process
        batch_delay: Delay between batches in seconds

    Returns:
        List of created HybridSearchDocument objects
    """
    if not models:
        return []

    batch_size = get_batch_size(searchable_type)
    backfill_fn = type_to_search_registration(searchable_type).search_function

    logger.info(
        f"Processing {len(models)} {searchable_type.value} models in batches of {batch_size}"
    )

    all_docs = []
    total_batches = (len(models) + batch_size - 1) // batch_size

    # Process models in batches
    for i in range(0, len(models), batch_size):
        batch_models = models[i : i + batch_size]
        batch_num = i // batch_size + 1

        logger.info(
            f"Processing batch {batch_num}/{total_batches} ({len(batch_models)} models)"
        )

        # Generate search documents for this batch
        batch_docs = []
        failed_models = []

        for model in batch_models:
            try:
                doc = backfill_fn(db, model)
                # Search wrappers swallow indexing errors and return None so
                # entity creates are not blocked; treat that as a failed model
                # here so we never flush null documents into the batch.
                if doc is None:
                    logger.error(
                        f"Failed to create search document for "
                        f"{searchable_type.value} {model.api_identifier}: "
                        f"search function returned None"
                    )
                    failed_models.append(model)
                    continue
                batch_docs.append(doc)
            except Exception as e:
                logger.error(
                    f"Failed to create search document for {searchable_type.value} {model.api_identifier}: {e}"
                )
                failed_models.append(model)
                continue

        # Commit this batch to avoid memory issues
        if batch_docs:
            db.add_all(batch_docs)
            db.flush()  # Flush to get IDs but don't commit yet
            all_docs.extend(batch_docs)

            logger.info(
                f"Successfully processed batch {batch_num} with {len(batch_docs)} {searchable_type.value} documents"
            )

        if failed_models:
            logger.warning(
                f"Failed to process {len(failed_models)} models in batch {batch_num}"
            )

        # Add delay between batches to respect rate limits
        if batch_num < total_batches:
            logger.info(f"Waiting {batch_delay}s before next batch...")
            import time

            time.sleep(batch_delay)

    logger.info(
        f"Completed processing {len(all_docs)} {searchable_type.value} documents"
    )
    return all_docs


def _truncate_search_documents(
    db: Session, searchable_type: SearchableType
) -> None:
    db.execute(
        delete(HybridSearchDocument).where(
            HybridSearchDocument.id.in_(
                select(HybridSearchDocument.id)
                .join(HybridSearchDocumentAssociation)
                .where(
                    HybridSearchDocumentAssociation.model_type
                    == searchable_type.value
                )
            )
        )
    )
