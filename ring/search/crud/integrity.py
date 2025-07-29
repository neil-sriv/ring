from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ring.async_scheduler.scheduler import (
    interval_job_factory,
    job_factory,
    scheduler,
)
from ring.lib.logger import logger
from ring.search.crud.hybrid_search import SEARCH_REGISTRY, SearchableType
from ring.search.models.hybrid_search import (
    HybridSearchDocument,
    HybridSearchDocumentAssociation,
)


@dataclass
class IntegrityCheckResult:
    """Result of an integrity check for a specific searchable type."""

    searchable_type: SearchableType
    missing_documents_count: int
    non_existent_references_count: int
    total_models_checked: int
    total_search_documents_found: int


def check_integrity_for_searchable_type(
    db: Session, searchable_type: SearchableType
) -> IntegrityCheckResult:
    """Check integrity for a specific searchable type.

    This function:
    1. Gets all models of the given type from the database
    2. Checks which models have search documents
    3. Checks which search documents reference non-existent models

    Args:
        db: Database session
        searchable_type: The searchable type to check

    Returns:
        IntegrityCheckResult: Results of the integrity check
    """
    registration = SEARCH_REGISTRY[searchable_type]
    model_class = registration.model_class

    # Get all models of this type
    models = db.scalars(select(model_class)).all()
    model_api_identifiers = [model.api_identifier for model in models]
    total_models_checked = len(model_api_identifiers)

    # Get all search document associations for this type
    associations = db.scalars(
        select(HybridSearchDocumentAssociation).where(
            HybridSearchDocumentAssociation.model_type == searchable_type.value
        )
    ).all()

    # Find missing search documents
    existing_search_identifiers = {
        assoc.model_api_identifier for assoc in associations
    }
    missing_identifiers = (
        set(model_api_identifiers) - existing_search_identifiers
    )
    missing_documents_count = len(missing_identifiers)

    # Find references to non-existent models
    non_existent_identifiers = existing_search_identifiers - set(
        model_api_identifiers
    )
    non_existent_references_count = len(non_existent_identifiers)

    total_search_documents_found = len(associations)

    logger.info(
        f"Integrity check for {searchable_type.value}: "
        f"{missing_documents_count} missing documents, "
        f"{non_existent_references_count} non-existent references, "
        f"{total_models_checked} models checked, "
        f"{total_search_documents_found} search documents found"
    )

    return IntegrityCheckResult(
        searchable_type=searchable_type,
        missing_documents_count=missing_documents_count,
        non_existent_references_count=non_existent_references_count,
        total_models_checked=total_models_checked,
        total_search_documents_found=total_search_documents_found,
    )


@job_factory("check_integrity_for_searchable_type")
def async_check_integrity_for_searchable_type(
    db: Session, searchable_type_value: str
) -> IntegrityCheckResult:
    """Async job to check integrity for a specific searchable type.

    Args:
        db: Database session
        searchable_type_value: String value of the searchable type

    Returns:
        IntegrityCheckResult: Results of the integrity check
    """
    searchable_type = SearchableType(searchable_type_value)
    return check_integrity_for_searchable_type(db, searchable_type)


@interval_job_factory("search_integrity_check", days=1)
def search_integrity_check(db: Session) -> dict[str, Any]:
    """Integrity check for search documents.

    This job will:
    - Check for any search documents that are missing from the database
    - Check for any search documents that reference a non-existent model
    - Kick off async tasks for each searchable type

    This job will be run daily at midnight.

    Returns:
        dict: Summary of the integrity check results
    """
    logger.info("Starting search integrity check")

    # Kick off async tasks for each searchable type
    for searchable_type in SearchableType:
        scheduler.add_job(
            async_check_integrity_for_searchable_type,
            args=[searchable_type.value],
        )

    logger.info(
        f"Kicked off {len(SearchableType)} async integrity check tasks"
    )

    return {
        "message": f"Kicked off {len(SearchableType)} async integrity check tasks",
        "searchable_types": [st.value for st in SearchableType],
    }
