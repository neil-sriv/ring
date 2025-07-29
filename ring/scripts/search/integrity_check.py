"""Script to run an adhoc search integrity check.

This script allows you to manually trigger a search integrity check to identify
missing search documents and non-existent references.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from ring.scripts.dependencies import (
    ScriptDependencies,
    get_script_dependencies,
    script_depends,
)
from ring.search.crud.integrity import (
    check_integrity_for_searchable_type,
    log_integrity_check_result,
)
from ring.search.models.hybrid_search import SearchableType


def run_script(
    deps: ScriptDependencies = script_depends(get_script_dependencies),
    searchable_type: str | None = None,
) -> dict[str, Any]:
    """Run a search integrity check.

    Args:
        deps: Script dependencies provided by script_depends
        searchable_type: Optional specific searchable type to check

    Returns:
        dict: Results of the integrity check
    """
    if searchable_type:
        # Run integrity check for specific type
        st = SearchableType(searchable_type)
        logger.info(f"Running integrity check for {searchable_type}")
        result = check_integrity_for_searchable_type(deps.db, st)

        # The result is already logged by the standardized function

        return {
            "searchable_type": result.searchable_type.value,
            "missing_documents_count": result.missing_documents_count,
            "non_existent_references_count": result.non_existent_references_count,
            "total_models_checked": result.total_models_checked,
            "total_search_documents_found": result.total_search_documents_found,
        }
    else:
        # Run integrity checks for all types
        logger.info("Running integrity checks for all searchable types")

        results = {}
        total_missing = 0
        total_non_existent = 0
        total_models = 0
        total_documents = 0

        for searchable_type_enum in SearchableType:
            try:
                result = check_integrity_for_searchable_type(
                    deps.db, searchable_type_enum
                )
                results[searchable_type_enum.value] = {
                    "searchable_type": result.searchable_type.value,
                    "missing_documents_count": result.missing_documents_count,
                    "non_existent_references_count": result.non_existent_references_count,
                    "total_models_checked": result.total_models_checked,
                    "total_search_documents_found": result.total_search_documents_found,
                }

                total_missing += result.missing_documents_count
                total_non_existent += result.non_existent_references_count
                total_models += result.total_models_checked
                total_documents += result.total_search_documents_found

                # Use standardized logging for individual results
                log_integrity_check_result(result)

            except Exception as e:
                logger.error(
                    f"Error checking integrity for {searchable_type_enum.value}: {e}"
                )
                results[searchable_type_enum.value] = {
                    "error": str(e),
                    "missing_documents_count": 0,
                    "non_existent_references_count": 0,
                    "total_models_checked": 0,
                    "total_search_documents_found": 0,
                }

        logger.info(
            f"Summary: {total_missing} total missing documents, "
            f"{total_non_existent} total non-existent references, "
            f"{total_models} total models checked, "
            f"{total_documents} total search documents found"
        )

        return {
            "results": results,
            "summary": {
                "total_missing_documents": total_missing,
                "total_non_existent_references": total_non_existent,
                "total_models_checked": total_models,
                "total_search_documents_found": total_documents,
            },
        }
