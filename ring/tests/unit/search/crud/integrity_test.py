"""Tests for search integrity check functionality."""

from __future__ import annotations

from sqlalchemy.orm import Session

from ring.search.crud.integrity import (
    IntegrityCheckResult,
    check_integrity_for_searchable_type,
    search_integrity_check,
)
from ring.search.models.hybrid_search import SearchableType
from ring.tests.factories.parties.user_factory import UserFactory
from ring.tests.lib.utils import assert_lists_equal_with_order_insensitive


class TestIntegrityCheckResult:
    """Test the IntegrityCheckResult dataclass."""

    def test_integrity_check_result_creation(self) -> None:
        """Test creating an IntegrityCheckResult."""
        result = IntegrityCheckResult(
            searchable_type=SearchableType.USER,
            missing_documents_count=5,
            non_existent_references_count=2,
            total_models_checked=100,
            total_search_documents_found=93,
        )

        assert result.searchable_type == SearchableType.USER
        assert result.missing_documents_count == 5
        assert result.non_existent_references_count == 2
        assert result.total_models_checked == 100
        assert result.total_search_documents_found == 93


class TestCheckIntegrityForSearchableType:
    """Test the check_integrity_for_searchable_type function."""

    def test_check_integrity_for_searchable_type(
        self,
        db_session: Session,
    ) -> None:
        """Test checking integrity for a searchable type."""
        users = [UserFactory() for _ in range(10)]
        db_session.add_all(users)
        db_session.commit()

        result = check_integrity_for_searchable_type(
            db_session, SearchableType.USER
        )

        assert result.searchable_type == SearchableType.USER
        assert result.missing_documents_count == 10
        assert result.non_existent_references_count == 0
        assert result.total_models_checked == 10
        assert result.total_search_documents_found == 0


class TestSearchIntegrityCheck:
    """Test the main search_integrity_check function."""

    def test_search_integrity_check(
        self,
        db_session: Session,
    ) -> None:
        """Test the main search integrity check function."""
        result = search_integrity_check()

        assert result["message"] == "Kicked off 5 async integrity check tasks"
        assert_lists_equal_with_order_insensitive(
            result["searchable_types"],
            [st.value for st in SearchableType],
        )
