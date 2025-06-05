"""Script to backfill search documents for all users, groups, letters, questions, and responses."""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ring.api_identifier.api_identified_model import APIIdentified
from ring.letters.crud import letter as letter_crud
from ring.lib.logger import logger
from ring.parties.crud import group as group_crud
from ring.parties.crud import user as user_crud
from ring.scripts.script_base import script_di
from ring.search.crud.hybrid_search import (
    type_to_search_registration,
)
from ring.search.models.hybrid_search import (
    HybridSearchDocument,
    SearchableType,
)


@script_di()
def run_script(
    db: Session,
    searchable_types: list[SearchableType] | None = None,
    replace_existing: bool = False,
    dry_run: bool = True,
) -> None:
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
    for searchable_type in searchable_types:
        model_class = type_to_search_registration(searchable_type).model_class
        models = db.scalars(select(model_class)).all()
        # partition models into those that have search documents and those that don't

        if replace_existing:
            _truncate_search_documents(db, searchable_type)
            _backfill_search_documents(db, searchable_type, models)
        else:
            _, models_without_documents = _partition_models_by_documents(
                db, models
            )
            _backfill_search_documents(
                db, searchable_type, models_without_documents
            )
    if dry_run:
        logger.info("Dry run, rolling back")
        db.rollback()
    else:
        db.commit()


def _partition_models_by_documents(
    db: Session, models: list[APIIdentified]
) -> tuple[list[APIIdentified], list[APIIdentified]]:
    models_with_documents = []
    models_without_documents = []
    associations = db.scalars(
        select(HybridSearchDocument).where(
            HybridSearchDocument.model_api_identifier.in_(
                [model.api_id for model in models]
            )
        )
    ).all()
    for model in models:
        if model.api_id in [
            association.model_api_identifier for association in associations
        ]:
            models_with_documents.append(model)
        else:
            models_without_documents.append(model)
    return models_with_documents, models_without_documents


def _backfill_search_documents(
    db: Session, searchable_type: SearchableType, models: list[APIIdentified]
) -> list[HybridSearchDocument]:
    docs = []
    backfill_fn = type_to_search_registration(searchable_type).search_function
    docs = [backfill_fn(db, model) for model in models]
    db.add_all(docs)
    return docs


def _truncate_search_documents(
    db: Session, searchable_type: SearchableType
) -> None:
    db.execute(
        delete(HybridSearchDocument).where(
            HybridSearchDocument.model_type == searchable_type.value
        )
    )
