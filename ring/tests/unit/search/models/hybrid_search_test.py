"""Tests for the hybrid search models.

This module contains tests for the hybrid search models' functionality,
including model creation, relationships, and computed columns.
It verifies both model attributes and relationships with other models.
"""

from __future__ import annotations

from datetime import UTC, datetime
from logging import Logger

import sqlalchemy
from faker import Faker
from sqlalchemy.orm import Session

from ring.search.models.hybrid_search import (
    HybridSearchDocument,
    HybridSearchDocumentAssociation,
    SearchableType,
)

TEST_CREATED_AT = datetime(2024, 6, 1, tzinfo=UTC)


class TestHybridSearchDocument:
    """Test suite for the hybrid search document model.

    This class contains tests for all hybrid search document model functionality,
    including model creation, relationships, and computed columns.
    """

    def test_hybrid_search_document_model(
        self, faker: Faker, db_session: Session
    ) -> None:
        """Test basic hybrid search document model creation and attributes.

        This test verifies that:
        1. A document can be created with raw text and embedding
        2. The document has the correct raw text and embedding
        3. The document has valid ID and creation timestamp
        4. The document is properly stored in the database

        Args:
            faker (Faker): Faker instance for generating test data
            db_session (Session): Database session
        """
        raw_text = faker.text()
        embedding = [0.1] * 768
        document = HybridSearchDocument.create(
            raw_text=raw_text,
            text_embedding_768=embedding,
        )
        db_session.add(document)
        db_session.commit()

        assert document.raw_text == raw_text
        assert len(document.text_embedding_768) == 768
        assert document.id is not None
        assert document.created_at is not None

        db_document = db_session.scalars(
            sqlalchemy.select(HybridSearchDocument).filter(
                HybridSearchDocument.id == document.id
            )
        ).one()
        assert db_document == document

    def test_hybrid_search_document_with_association(
        self, faker: Faker, db_session: Session
    ) -> None:
        """Test hybrid search document's relationship with associations.

        This test verifies that:
        1. A new document has no associations
        2. An association can be created and linked to the document
        3. The document can access its associations
        4. The relationship is properly stored

        Args:
            faker (Faker): Faker instance for generating test data
            db_session (Session): Database session
        """
        raw_text = faker.text()
        embedding = [0.1] * 768
        document = HybridSearchDocument.create(
            raw_text=raw_text,
            text_embedding_768=embedding,
        )
        db_session.add(document)
        db_session.commit()

        assert document.associations == []

        association = HybridSearchDocumentAssociation.create(
            model_api_identifier="test_id",
            model_type=SearchableType.USER.value,
            hybrid_search_document=document,
            entity_created_at=TEST_CREATED_AT,
        )
        db_session.add(association)
        db_session.commit()

        assert document.associations == [association]
        assert association.document == document


class TestHybridSearchDocumentAssociation:
    """Test suite for the hybrid search document association model.

    This class contains tests for all hybrid search document association model functionality,
    including model creation and relationships.
    """

    def test_hybrid_search_document_association_model(
        self, faker: Faker, db_session: Session
    ) -> None:
        """Test basic hybrid search document association model creation and attributes.

        This test verifies that:
        1. An association can be created with model API identifier, type, and document
        2. The association has the correct model API identifier and type
        3. The association has valid ID
        4. The association is properly stored in the database

        Args:
            faker (Faker): Faker instance for generating test data
            db_session (Session): Database session
        """
        raw_text = faker.text()
        embedding = [0.1] * 768
        document = HybridSearchDocument.create(
            raw_text=raw_text,
            text_embedding_768=embedding,
        )
        db_session.add(document)
        db_session.commit()

        association = HybridSearchDocumentAssociation.create(
            model_api_identifier="test_id",
            model_type=SearchableType.USER.value,
            hybrid_search_document=document,
            entity_created_at=TEST_CREATED_AT,
        )
        db_session.add(association)
        db_session.commit()

        assert association.model_api_identifier == "test_id"
        assert association.model_type == SearchableType.USER.value
        assert association.hybrid_search_document_id == document.id
        assert association.id is not None

        db_association = db_session.scalars(
            sqlalchemy.select(HybridSearchDocumentAssociation).filter(
                HybridSearchDocumentAssociation.id == association.id
            )
        ).one()
        assert db_association == association
