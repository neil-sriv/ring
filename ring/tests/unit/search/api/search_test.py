"""Tests for the search API endpoints.

This module contains tests for all search-related API endpoints,
including raw search and hydrated search functionality.
It verifies both successful operations and error cases.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.letters.constants import LetterStatus
from ring.parties.models.user_model import User
from ring.search.crud.hybrid_search import (
    HybridSearchDocument,
    HybridSearchDocumentAssociation,
    SearchableType,
    create_hybrid_search_document,
)
from ring.search.schemas.search import SearchHit, SearchResponse
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory
from ring.tests.lib.utils import (
    assert_pydantic_schema_json_dump_equivalent_to_response_dict,
)


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

    def test_raw_search_requires_authentication(
        self,
        unauthenticated_client: TestClient,
    ) -> None:
        response = unauthenticated_client.get(
            "/search/raw-search?query=test&search_type=keyword"
        )

        assert response.status_code == 401

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
                results=[SearchHit.from_model(user) for user in users[:2]],
                total=2,
            ),
            data,
        )

    @patch("ring.search.crud.hybrid_search._generate_text_embedding")
    def test_hydrated_search_offset_pagination(
        self,
        mock_generate_embedding: MagicMock,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        """Test paginating hydrated search results with limit and offset.

        This test verifies that:
        1. Consecutive pages return consecutive slices of the ranked results
        2. A partial final page returns only the remaining results
        3. An offset past the end of the results returns an empty page

        Args:
            mock_generate_embedding (MagicMock): Mock for embedding generation
            authenticated_client (TestClient): Authenticated test client
            current_user (User): Authenticated user performing the search
            db_session (Session): Database session
        """
        users = [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create()
        for user in users:
            group.members.append(user)
        group.members.append(current_user)
        db_session.commit()

        base_embedding = [0.1] * 768
        for i, user in enumerate(users):
            doc_embedding = [x + (i * 0.01) for x in base_embedding]
            document = HybridSearchDocument.create(
                raw_text=f"test document for {user.name}",
                text_embedding_768=doc_embedding,
            )
            association = HybridSearchDocumentAssociation.create(
                model_api_identifier=user.api_identifier,
                model_type=SearchableType.USER.value,
                hybrid_search_document=document,
            )
            db_session.add_all([document, association])
        db_session.commit()

        query_embedding = [x + 0.005 for x in base_embedding]
        mock_generate_embedding.return_value = query_embedding

        first_page = authenticated_client.get(
            "/search/search?query=test&search_type=semantic&limit=2&offset=0"
        )

        assert first_page.status_code == 200
        assert_pydantic_schema_json_dump_equivalent_to_response_dict(
            SearchResponse(
                results=[SearchHit.from_model(user) for user in users[:2]],
                total=2,
            ),
            first_page.json(),
        )

        second_page = authenticated_client.get(
            "/search/search?query=test&search_type=semantic&limit=2&offset=2"
        )

        assert second_page.status_code == 200
        assert_pydantic_schema_json_dump_equivalent_to_response_dict(
            SearchResponse(
                results=[SearchHit.from_model(users[2])],
                total=1,
            ),
            second_page.json(),
        )

        empty_page = authenticated_client.get(
            "/search/search?query=test&search_type=semantic&limit=2&offset=4"
        )

        assert empty_page.status_code == 200
        empty_data = empty_page.json()
        assert empty_data["total"] == 0
        assert empty_data["results"] == []

    def test_hydrated_search_type_filter(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        """Test filtering hydrated search results by result type.

        This test verifies that:
        1. A single type filter returns only results of that type
        2. A multi-select filter (repeated types params) returns all selected
           types, preserving rank order
        3. A filter matching no documents returns an empty result

        Args:
            authenticated_client (TestClient): Authenticated test client
            current_user (User): Authenticated user performing the search
            db_session (Session): Database session
        """
        users = [UserFactory.create() for _ in range(2)]
        group = GroupFactory.create()
        for user in users:
            group.members.append(user)
        group.members.append(current_user)
        db_session.commit()

        # The autouse embedding mock returns [0.1] * 768 for the query, so
        # increasing per-document offsets give a deterministic rank order:
        # users[0], users[1], then the group.
        base_embedding = [0.1] * 768
        document_specs = [
            (users[0].api_identifier, SearchableType.USER, 0.001),
            (users[1].api_identifier, SearchableType.USER, 0.002),
            (group.api_identifier, SearchableType.GROUP, 0.003),
        ]
        for model_api_identifier, model_type, offset in document_specs:
            document = HybridSearchDocument.create(
                raw_text=f"test document for {model_api_identifier}",
                text_embedding_768=[x + offset for x in base_embedding],
            )
            association = HybridSearchDocumentAssociation.create(
                model_api_identifier=model_api_identifier,
                model_type=model_type.value,
                hybrid_search_document=document,
            )
            db_session.add_all([document, association])
        db_session.commit()

        group_only = authenticated_client.get(
            "/search/search?query=test&search_type=semantic&limit=10"
            "&types=group"
        )

        assert group_only.status_code == 200
        assert_pydantic_schema_json_dump_equivalent_to_response_dict(
            SearchResponse(
                results=[SearchHit.from_model(group)],
                total=1,
            ),
            group_only.json(),
        )

        users_and_group = authenticated_client.get(
            "/search/search?query=test&search_type=semantic&limit=10"
            "&types=user&types=group"
        )

        assert users_and_group.status_code == 200
        assert_pydantic_schema_json_dump_equivalent_to_response_dict(
            SearchResponse(
                results=[
                    SearchHit.from_model(users[0]),
                    SearchHit.from_model(users[1]),
                    SearchHit.from_model(group),
                ],
                total=3,
            ),
            users_and_group.json(),
        )

        no_matches = authenticated_client.get(
            "/search/search?query=test&search_type=semantic&limit=10"
            "&types=response"
        )

        assert no_matches.status_code == 200
        no_matches_data = no_matches.json()
        assert no_matches_data["total"] == 0
        assert no_matches_data["results"] == []

    def test_hydrated_search_author_and_status_qualifiers(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        """GitHub-style author: and status: qualifiers filter hydrated hits."""
        group = GroupFactory.create()
        zelda = UserFactory.create(name="Zelda Qualifier")
        marcus = UserFactory.create(name="Marcus Qualifier")
        group.members.extend([current_user, zelda, marcus])
        open_letter = LetterFactory.create(
            group=group, status=LetterStatus.IN_PROGRESS
        )
        published_letter = LetterFactory.create(
            group=group, status=LetterStatus.SENT
        )
        zelda_open = QuestionFactory.create(
            letter=open_letter,
            author=zelda,
            question_text="Bandicoot breakfast on the open issue?",
        )
        zelda_published = QuestionFactory.create(
            letter=published_letter,
            author=zelda,
            question_text="Bandicoot breakfast on the published issue?",
        )
        marcus_open = QuestionFactory.create(
            letter=open_letter,
            author=marcus,
            question_text="Bandicoot breakfast from someone else?",
        )
        for question in (zelda_open, zelda_published, marcus_open):
            create_hybrid_search_document(
                db_session,
                raw_text=question.question_text,
                model_api_identifier=question.api_identifier,
                model_type=SearchableType.QUESTION,
            )
        db_session.commit()

        author_response = authenticated_client.get(
            "/search/search",
            params={
                "query": "bandicoot author:Zelda",
                "search_type": "keyword",
                "limit": 10,
            },
        )
        assert author_response.status_code == 200
        author_ids = {
            hit["api_identifier"] for hit in author_response.json()["results"]
        }
        assert zelda_open.api_identifier in author_ids
        assert zelda_published.api_identifier in author_ids
        assert marcus_open.api_identifier not in author_ids

        status_response = authenticated_client.get(
            "/search/search",
            params={
                "query": "bandicoot status:open",
                "search_type": "keyword",
                "limit": 10,
            },
        )
        assert status_response.status_code == 200
        status_ids = {
            hit["api_identifier"] for hit in status_response.json()["results"]
        }
        assert status_ids == {
            zelda_open.api_identifier,
            marcus_open.api_identifier,
        }

        combined_response = authenticated_client.get(
            "/search/search",
            params={
                "query": "bandicoot author:Zelda status:published",
                "search_type": "keyword",
                "limit": 10,
            },
        )
        assert combined_response.status_code == 200
        combined_ids = {
            hit["api_identifier"]
            for hit in combined_response.json()["results"]
        }
        assert combined_ids == {zelda_published.api_identifier}
