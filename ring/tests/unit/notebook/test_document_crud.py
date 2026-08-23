"""Tests for document CRUD operations.

This module contains tests for all document-related database operations,
including document creation, updates, and edit management.
It verifies both successful operations and error cases.
"""

from __future__ import annotations

import sqlalchemy
from faker import Faker
from sqlalchemy.orm import Session

from ring.notebook.crud.document import (
    create_document,
    get_documents,
    update_document,
)
from ring.notebook.models.document import Document
from ring.tests.factories.notebook.document_factory import DocumentFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory


class TestDocumentCRUD:
    """Test suite for document CRUD operations.

    This class contains tests for all document-related database operations,
    including CRUD operations and edit management.
    """

    def test_create_document(self, db_session: Session, faker: Faker) -> None:
        """Test creating a new document.

        This test verifies that:
        1. A document can be created with valid name and content
        2. The document has the correct attributes
        3. The document is properly stored in the database
        4. The document can be retrieved after creation

        Args:
            db_session (Session): Database session
            faker (Faker): Faker instance for generating test data
        """
        user = UserFactory.create()
        group = GroupFactory.create()
        db_session.commit()

        name, content = (
            faker.sentence(nb_words=3),
            faker.text(max_nb_chars=500),
        )
        document = create_document(db_session, name, content, user, group)
        db_session.commit()

        assert document.name == name
        assert document.content == content.encode("utf-8")
        assert document.latest_snapshot_version == 0

        # Verify document was created in database
        db_document = db_session.scalar(
            sqlalchemy.select(Document).filter(Document.name == name)
        )
        assert db_document is not None
        assert db_document.name == name
        assert db_document.content.decode("utf-8") == content

    def test_create_document_with_empty_content(
        self, db_session: Session, faker: Faker
    ) -> None:
        """Test creating a document with empty content.

        This test verifies that:
        1. A document can be created with empty content
        2. The document has the correct attributes
        3. The document is properly stored in the database
        4. Empty content is handled correctly

        Args:
            db_session (Session): Database session
            faker (Faker): Faker instance for generating test data
        """
        user = UserFactory.create()
        group = GroupFactory.create()
        db_session.commit()

        name = faker.sentence(nb_words=3)
        content = ""
        document = create_document(db_session, name, content, user, group)
        db_session.commit()

        assert document.name == name
        assert document.content == content.encode("utf-8")
        assert document.latest_snapshot_version == 0

    def test_update_document_name_only(
        self, db_session: Session, faker: Faker
    ) -> None:
        """Test updating only the document name.

        This test verifies that:
        1. A document's name can be updated independently
        2. The document's content remains unchanged
        3. The version remains unchanged when only name is updated
        4. The database state is updated correctly

        Args:
            db_session (Session): Database session
            faker (Faker): Faker instance for generating test data
        """
        document = DocumentFactory.create()
        db_session.commit()

        new_name = faker.sentence(nb_words=3)
        original_content = document.content
        original_version = document.latest_snapshot_version

        updated_document = update_document(db_session, document, name=new_name)
        db_session.commit()

        assert updated_document.name == new_name
        assert updated_document.content == original_content
        assert updated_document.latest_snapshot_version == original_version

    def test_update_document_content_only(
        self, db_session: Session, faker: Faker
    ) -> None:
        """Test updating only the document content.

        This test verifies that:
        1. A document's content can be updated independently
        2. The document's name remains unchanged
        3. The version is incremented when content changes
        4. The database state is updated correctly

        Args:
            db_session (Session): Database session
            faker (Faker): Faker instance for generating test data
        """
        document = DocumentFactory.create()
        db_session.commit()

        new_content = faker.text(max_nb_chars=500)
        original_name = document.name
        original_version = document.latest_snapshot_version

        updated_document = update_document(
            db_session, document, content=new_content
        )
        db_session.commit()

        assert updated_document.name == original_name
        assert updated_document.content == new_content.encode("utf-8")
        assert (
            updated_document.latest_snapshot_version == original_version
        )  # No auto-increment

    def test_update_document_both_fields(
        self, db_session: Session, faker: Faker
    ) -> None:
        """Test updating both document name and content.

        This test verifies that:
        1. Both name and content can be updated simultaneously
        2. The version is incremented when content changes
        3. The database state is updated correctly
        4. All changes are reflected in the document

        Args:
            db_session (Session): Database session
            faker (Faker): Faker instance for generating test data
        """
        document = DocumentFactory.create()
        db_session.commit()

        new_name = faker.sentence(nb_words=3)
        new_content = faker.text(max_nb_chars=500)
        original_version = document.latest_snapshot_version

        updated_document = update_document(
            db_session, document, name=new_name, content=new_content
        )
        db_session.commit()

        assert updated_document.name == new_name
        assert updated_document.content == new_content.encode("utf-8")
        assert (
            updated_document.latest_snapshot_version == original_version
        )  # No auto-increment

    def test_update_document_no_changes(self, db_session: Session) -> None:
        """Test updating a document with no changes.

        This test verifies that:
        1. Updating a document with no changes works correctly
        2. The document remains unchanged
        3. The version remains unchanged
        4. The database state remains unchanged

        Args:
            db_session (Session): Database session
        """
        document = DocumentFactory.create()
        db_session.commit()

        original_name = document.name
        original_content = document.content
        original_version = document.latest_snapshot_version

        updated_document = update_document(db_session, document)
        db_session.commit()

        assert updated_document.name == original_name
        assert updated_document.content == original_content
        assert updated_document.latest_snapshot_version == original_version

    def test_get_documents(self, db_session: Session) -> None:
        """Test getting documents for a group.

        This test verifies that:
        1. Documents can be retrieved for a group
        2. The documents have the correct attributes
        3. The documents are properly stored in the database
        """
        group = GroupFactory.create()
        db_session.commit()
        assert get_documents(db_session, group) == []

        documents = [DocumentFactory.create(group=group) for _ in range(3)]
        db_session.commit()
        assert get_documents(db_session, group) == documents
