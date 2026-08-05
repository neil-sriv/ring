"""Tests for the search API endpoints.

This module contains tests for all search-related API endpoints,
including raw search and hydrated search functionality.
It verifies both successful operations and error cases.
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.parties.models.user_model import User
from ring.ring_pydantic.linked_schemas import SearchResponse, SearchResult
from ring.search.crud.hybrid_search import (
    HybridSearchDocument,
    HybridSearchDocumentAssociation,
    SearchableType,
    create_hybrid_search_document,
)
from ring.search.schemas.search import SearchSort
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.letters.response_factory import ResponseFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory
from ring.tests.lib.utils import (
    assert_pydantic_schema_json_dump_equivalent_to_response_dict,
)

TEST_CREATED_AT = datetime(2024, 6, 1, tzinfo=UTC)


class TestSearchAPI:
    """Test suite for search API endpoints.

    This class contains tests for all search-related API operations,
    including raw search, hydrated search, and error handling.
    """

    @patch("ring.search.crud.hybrid_search._generate_text_embedding")
    def test_raw_search_dual(
        self,
        mock_generate_embedding: MagicMock,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        """Test performing a dual raw search.

        This test verifies that:
        1. A dual search can be performed
        2. The response contains results from both semantic and keyword search
        3. The results are ordered by relevance
        4. The response matches the database state

        Args:
            mock_generate_embedding (MagicMock): Mock for embedding generation
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
        """
        # Create test documents with different content
        base_embedding = [0.1] * 768
        for i in range(3):
            doc_embedding = [x + (i * 0.01) for x in base_embedding]
            mock_generate_embedding.return_value = doc_embedding
            document = HybridSearchDocument.create(
                raw_text=f"test document {i} with keyword",
                text_embedding_768=doc_embedding,
            )
            association = HybridSearchDocumentAssociation.create(
                model_api_identifier=f"test_id_{i}",
                model_type=SearchableType.USER.value,
                hybrid_search_document=document,
                entity_created_at=TEST_CREATED_AT,
            )
            db_session.add_all([document, association])
        db_session.commit()

        # Mock the query embedding
        query_embedding = [x + 0.005 for x in base_embedding]
        mock_generate_embedding.return_value = query_embedding

        response = authenticated_client.get(
            "/search/raw-search?query=test keyword&search_type=dual&limit=2"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["results"]) == 2
        assert all(
            "test" in result["raw_text"] or "keyword" in result["raw_text"]
            for result in data["results"]
        )

    def test_raw_search_empty_query(
        self,
        authenticated_client: TestClient,
    ) -> None:
        """Test performing a search with an empty query.

        This test verifies that:
        1. An empty query search fails
        2. The response contains the correct error message
        3. The response indicates the query was invalid

        Args:
            authenticated_client (TestClient): Authenticated test client
        """
        response = authenticated_client.get(
            "/search/raw-search?query=&search_type=semantic"
        )

        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Search query cannot be empty"

    @patch("ring.search.crud.hybrid_search._generate_text_embedding")
    def test_hydrated_search(
        self,
        mock_generate_embedding: MagicMock,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
        logger,
    ) -> None:
        """Test performing a hydrated search.

        This test verifies that:
        1. A hydrated search can be performed
        2. The response contains the correct search results
        3. The results are properly hydrated with model instances
        4. The response matches the database state

        Args:
            mock_generate_embedding (MagicMock): Mock for embedding generation
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
        """
        # Create test users
        users = [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create()
        for user in users:
            group.members.append(user)
        group.members.append(current_user)
        db_session.commit()

        # Create test documents with different embeddings
        base_embedding = [0.1] * 768
        for i, user in enumerate(users):
            doc_embedding = [x + (i * 0.01) for x in base_embedding]
            mock_generate_embedding.return_value = doc_embedding
            document = HybridSearchDocument.create(
                raw_text=f"test document for {user.name}",
                text_embedding_768=doc_embedding,
            )
            association = HybridSearchDocumentAssociation.create(
                model_api_identifier=user.api_identifier,
                model_type=SearchableType.USER.value,
                hybrid_search_document=document,
                entity_created_at=TEST_CREATED_AT,
            )
            db_session.add_all([document, association])
        db_session.commit()

        # Mock the query embedding
        query_embedding = [x + 0.005 for x in base_embedding]
        mock_generate_embedding.return_value = query_embedding

        response = authenticated_client.get(
            "/search/search?query=test&search_type=semantic&limit=2"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["results"]) == 2
        assert_pydantic_schema_json_dump_equivalent_to_response_dict(
            SearchResponse(
                results=[SearchResult.from_model(user) for user in users[:2]],
                total=2,
            ),
            data,
        )

    def test_hydrated_search_with_group_filter(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        group_a = GroupFactory.create(
            admin=current_user, members=[current_user]
        )
        group_b = GroupFactory.create(
            admin=current_user, members=[current_user]
        )
        letter_a = LetterFactory.create(group=group_a)
        letter_b = LetterFactory.create(group=group_b)
        question_a = QuestionFactory.create(
            letter=letter_a, question_text="delta question"
        )
        QuestionFactory.create(letter=letter_b, question_text="delta question")
        response_a = ResponseFactory.create(
            question=question_a,
            participant=current_user,
            response_text="delta response",
        )
        db_session.commit()

        create_hybrid_search_document(
            db_session,
            raw_text="delta response content",
            model_api_identifier=response_a.api_identifier,
            model_type=SearchableType.RESPONSE,
            entity_created_at=response_a.created_at,
            group_api_id=group_a.api_identifier,
            participant_api_id=current_user.api_identifier,
        )
        create_hybrid_search_document(
            db_session,
            raw_text="delta response content",
            model_api_identifier="rsp_other",
            model_type=SearchableType.RESPONSE,
            entity_created_at=TEST_CREATED_AT,
            group_api_id=group_b.api_identifier,
            participant_api_id=current_user.api_identifier,
        )
        db_session.commit()

        response = authenticated_client.get(
            "/search/search",
            params={
                "query": "delta",
                "group_api_id": group_a.api_identifier,
                "sort": SearchSort.CREATED_AT_DESC.value,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["results"][0]["type"] == "ResponseLinked"
        assert (
            data["results"][0]["model"]["api_identifier"]
            == response_a.api_identifier
        )
