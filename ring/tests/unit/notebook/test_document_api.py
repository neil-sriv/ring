"""Tests for document API endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from ring.fastapp.fast import app
from ring.notebook.schemas.document import DocumentCreate, DocumentUpdate

client = TestClient(app)


class TestDocumentAPI:
    """Test cases for document API endpoints."""

    def test_create_document_schema(self):
        """Test that DocumentCreate schema works correctly."""
        document_data = {
            "name": "Test Document",
            "content": "This is a test document content.",
        }
        document = DocumentCreate(**document_data)
        assert document.name == "Test Document"
        assert document.content == "This is a test document content."

    def test_update_document_schema(self):
        """Test that DocumentUpdate schema works correctly."""
        update_data = {
            "name": "Updated Document Name",
            "content": "Updated content.",
        }
        update = DocumentUpdate(**update_data)
        assert update.name == "Updated Document Name"
        assert update.content == "Updated content."

    def test_document_schemas_optional_fields(self):
        """Test that DocumentUpdate schema allows partial updates."""
        update_data = {"name": "Only Name Update"}
        update = DocumentUpdate(**update_data)
        assert update.name == "Only Name Update"
        assert update.content is None

        update_data = {"content": "Only Content Update"}
        update = DocumentUpdate(**update_data)
        assert update.name is None
        assert update.content == "Only Content Update"
