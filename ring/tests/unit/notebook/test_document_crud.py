"""Tests for document CRUD operations."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from ring.notebook.crud.document import (
    add_document_edit,
    create_document,
    update_document,
)
from ring.notebook.models.document import Document, DocumentEdit
from ring.parties.models.user_model import User


class TestDocumentCRUD:
    """Test cases for document CRUD operations."""

    def test_create_document(self):
        """Test creating a new document."""
        # Mock dependencies
        mock_db = Mock()
        mock_user = Mock(spec=User)
        mock_user.api_identifier = "user123"

        # Test data
        name = "Test Document"
        content = "Test content"

        # Create document
        document = create_document(mock_db, name, content, mock_user)

        # Verify document was created correctly
        assert document.name == name
        assert document.content == content.encode("utf-8")
        assert document.latest_snapshot_version == 1

        # Verify it was added to the database
        mock_db.add.assert_called()

    def test_update_document_name_only(self):
        """Test updating only the document name."""
        # Mock document
        mock_document = Mock(spec=Document)
        mock_document.name = "Old Name"
        mock_document.content = b"Old content"
        mock_document.latest_snapshot_version = 1

        # Mock database
        mock_db = Mock()

        # Update document name only
        new_name = "New Name"
        updated_document = update_document(
            mock_db, mock_document, name=new_name
        )

        # Verify only name was updated
        assert updated_document.name == new_name
        assert updated_document.content == b"Old content"
        assert updated_document.latest_snapshot_version == 1

        # Verify it was added to the database
        mock_db.add.assert_called_once_with(mock_document)

    def test_update_document_content_only(self):
        """Test updating only the document content."""
        # Mock document
        mock_document = Mock(spec=Document)
        mock_document.name = "Test Document"
        mock_document.content = b"Old content"
        mock_document.latest_snapshot_version = 1

        # Mock database
        mock_db = Mock()

        # Update document content only
        new_content = "New content"
        updated_document = update_document(
            mock_db, mock_document, content=new_content
        )

        # Verify only content was updated
        assert updated_document.name == "Test Document"
        assert updated_document.content == new_content.encode("utf-8")
        assert updated_document.latest_snapshot_version == 2

        # Verify it was added to the database
        mock_db.add.assert_called_once_with(mock_document)

    def test_add_document_edit(self):
        """Test adding an edit to a document."""
        # Mock document
        mock_document = Mock(spec=Document)
        mock_document.latest_snapshot_version = 1
        mock_document.created_at = "2023-01-01T00:00:00Z"
        mock_document.updated_at = None

        # Mock user
        mock_user = Mock(spec=User)

        # Mock database
        mock_db = Mock()

        # Add edit
        delta = "Added new content"
        edit = add_document_edit(mock_db, mock_document, delta, mock_user)

        # Verify edit was created correctly
        assert edit.delta == delta.encode("utf-8")
        assert edit.version == 2
        assert edit.document == mock_document
        assert edit.author == mock_user

        # Verify document version was incremented
        assert mock_document.latest_snapshot_version == 2

        # Verify both were added to the database
        assert mock_db.add.call_count == 2
