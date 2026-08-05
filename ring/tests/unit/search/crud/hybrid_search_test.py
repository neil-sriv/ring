"""Tests for the hybrid search CRUD operations.

This module contains tests for the hybrid search CRUD operations,
including document creation, search functionality, and result hydration.
It verifies both basic operations and edge cases.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from faker import Faker
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import Session

from ring.authz.enforcer import Action
from ring.search.crud.hybrid_search import (
    create_hybrid_search_document,
    get_model_ids_from_hybrid_search_documents,
    hydrate_results,
    register_search_function,
    search,
    semantic_search_hybrid_search_document,
    type_to_search_registration,
)
from ring.search.models.hybrid_search import (
    HybridSearchDocument,
    HybridSearchDocumentAssociation,
    SearchableType,
)
from ring.search.schemas.search import SearchType
from ring.tests.factories.parties.user_factory import UserFactory


class TestHybridSearchCRUD:
    """Test suite for the hybrid search CRUD operations.

    This class contains tests for all hybrid search CRUD functionality,
    including document creation, search, and result hydration.
    """

    @patch("ring.search.crud.hybrid_search._generate_text_embedding")
    def test_create_hybrid_search_document(
        self,
        mock_generate_embedding: MagicMock,
        faker: Faker,
        db_session: Session,
    ) -> None:
        """Test creating a hybrid search document.

        Semantic/embedding search is deprecated, so document creation indexes
        for keyword search only. This test verifies that:
        1. A document can be created with raw text and model info
        2. No embedding is generated (the embedding service is not called)
        3. The association is properly created and linked

        Args:
            mock_generate_embedding (MagicMock): Mock for embedding generation
            faker (Faker): Faker instance for generating test data
            db_session (Session): Database session
        """
        raw_text = faker.text()

        document = create_hybrid_search_document(
            db_session,
            raw_text=raw_text,
            model_api_identifier="test_id",
            model_type=SearchableType.USER,
        )

        assert document.raw_text == raw_text
        assert document.text_embedding_768 is None
        mock_generate_embedding.assert_not_called()
        assert len(document.associations) == 1
        assert document.associations[0].model_api_identifier == "test_id"
        assert document.associations[0].model_type == SearchableType.USER.value

    @patch("ring.search.crud.hybrid_search._generate_text_embedding")
    def test_semantic_search_hybrid_search_document(
        self,
        mock_generate_embedding: MagicMock,
        faker: Faker,
        db_session: Session,
    ) -> None:
        """Test semantic search functionality.

        This test verifies that:
        1. Documents can be searched using semantic similarity
        2. Results are ordered by similarity
        3. Results respect the limit parameter

        Args:
            mock_generate_embedding (MagicMock): Mock for embedding generation
            faker (Faker): Faker instance for generating test data
            db_session (Session): Database session
        """
        # Create test documents with different embeddings. Embeddings are set
        # directly here because document creation no longer generates them
        # (semantic search is deprecated); semantic search still works for any
        # documents that do carry an embedding.
        documents = []
        base_embedding = [0.1] * 768
        for i in range(3):
            # Create embeddings that are increasingly different from the query
            # but still within the L2 distance threshold of 0.5
            doc_embedding = [x + (i * 0.01) for x in base_embedding]
            document = HybridSearchDocument.create(
                raw_text=f"test document {i}",
                text_embedding_768=doc_embedding,
            )
            association = HybridSearchDocumentAssociation.create(
                model_api_identifier=f"test_id_{i}",
                model_type=SearchableType.USER.value,
                hybrid_search_document=document,
            )
            db_session.add_all([document, association])
            documents.append(document)
        db_session.commit()

        # Mock the query embedding to be similar to the first two documents
        # but still within the L2 distance threshold
        query_embedding = [
            x + 0.005 for x in base_embedding
        ]  # Between doc 0 and 1
        mock_generate_embedding.return_value = query_embedding

        results = semantic_search_hybrid_search_document(
            db_session, "test query", limit=2
        )

        assert len(results) == 2
        assert all(isinstance(doc, HybridSearchDocument) for doc in results)
        # Verify results are ordered by similarity (first two documents should be closest)
        assert results[0].raw_text == "test document 0"
        assert results[1].raw_text == "test document 1"

    def test_get_model_ids_from_hybrid_search_documents(
        self, faker: Faker, db_session: Session
    ) -> None:
        """Test getting model IDs from search documents.

        This test verifies that:
        1. Model IDs are correctly extracted from search documents
        2. Results are grouped by model type
        3. All associations are properly processed

        Args:
            faker (Faker): Faker instance for generating test data
            db_session (Session): Database session
        """
        # Create test documents with associations
        documents = []
        for i in range(2):
            document = HybridSearchDocument.create(
                raw_text=f"test document {i}",
                text_embedding_768=[0.1] * 768,
            )
            association = HybridSearchDocumentAssociation.create(
                model_api_identifier=f"test_id_{i}",
                model_type=SearchableType.USER.value,
                hybrid_search_document=document,
            )
            db_session.add_all([document, association])
            documents.append(document)
        db_session.commit()

        model_ids = get_model_ids_from_hybrid_search_documents(
            db_session, documents
        )

        assert SearchableType.USER in model_ids
        assert len(model_ids[SearchableType.USER]) == 2
        assert "test_id_0" in model_ids[SearchableType.USER]
        assert "test_id_1" in model_ids[SearchableType.USER]

    def test_hydrate_results(
        self,
        faker: Faker,
        db_session: Session,
    ) -> None:
        """Test hydrating search results.

        This test verifies that:
        1. Model IDs are correctly hydrated into model instances
        2. The correct model class is used for hydration
        3. Results are returned in the expected format

        Args:
            faker (Faker): Faker instance for generating test data
            db_session (Session): Database session
        """
        models = [UserFactory.create() for _ in range(2)]
        db_session.commit()
        model_ids = [model.api_identifier for model in models]

        results = hydrate_results(
            db_session,
            SearchableType.USER,
            model_ids,
        )

        assert results == models

    @patch("ring.search.crud.hybrid_search.dual_search_hybrid_search_document")
    @patch(
        "ring.search.crud.hybrid_search.get_model_ids_from_hybrid_search_documents"
    )
    @patch("ring.search.crud.hybrid_search.hydrate_results")
    @patch("ring.search.crud.hybrid_search.filter_to_authorized")
    def test_search(
        self,
        mock_filter_authorized: MagicMock,
        mock_hydrate: MagicMock,
        mock_get_model_ids: MagicMock,
        mock_dual_search: MagicMock,
        faker: Faker,
        db_session: Session,
    ) -> None:
        """Test the main search function.

        This test verifies that:
        1. The search pipeline is executed correctly
        2. Results are properly hydrated
        3. The search type parameter is respected
        4. Authorization filtering is applied

        Args:
            mock_filter_authorized (MagicMock): Mock for authorization filtering
            mock_hydrate (MagicMock): Mock for result hydration
            mock_get_model_ids (MagicMock): Mock for model ID extraction
            mock_dual_search (MagicMock): Mock for dual search
            faker (Faker): Faker instance for generating test data
            db_session (Session): Database session
        """
        mock_documents = [MagicMock(), MagicMock()]
        mock_dual_search.return_value = mock_documents

        mock_model_ids = {SearchableType.USER: ["test_id_1", "test_id_2"]}
        mock_get_model_ids.return_value = mock_model_ids

        mock_hydrated = [MagicMock(), MagicMock()]
        mock_hydrate.return_value = mock_hydrated

        # Mock authorization filtering to return the hydrated results
        mock_filter_authorized.return_value = mock_hydrated

        user = UserFactory.create()
        results = search(
            db_session,
            "test query",
            user=user,
            limit=10,
            search_type=SearchType.DUAL,
        )

        assert results == mock_hydrated
        mock_dual_search.assert_called_once_with(db_session, "test query", 10)
        mock_get_model_ids.assert_called_once_with(db_session, mock_documents)
        mock_hydrate.assert_called_once()
        mock_filter_authorized.assert_called_once_with(
            db_session, user, Action.READ, mock_hydrated
        )

    def test_register_search_function_returns_none_on_error(
        self, db_session: Session
    ) -> None:
        """Search wrappers swallow indexing errors so entity creates proceed.

        Verifies that a failing registered search function returns None instead
        of raising, matching the Optional return type callers must handle.
        """
        from ring.parties.models.user_model import User
        from ring.search.crud import hybrid_search as hybrid_search_crud

        original = hybrid_search_crud.SEARCH_REGISTRY[
            SearchableType.USER.value
        ]

        @register_search_function(SearchableType.USER, User)
        def _failing_search(db: Session, model: User) -> HybridSearchDocument:
            raise RuntimeError("indexing failed")

        try:
            user = UserFactory.create()
            db_session.commit()
            result = type_to_search_registration(
                SearchableType.USER
            ).search_function(db_session, user)
            assert result is None
        finally:
            hybrid_search_crud.SEARCH_REGISTRY[SearchableType.USER.value] = (
                original
            )
