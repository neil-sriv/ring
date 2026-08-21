"""Tests for document API endpoints.

This module contains tests for all document-related API endpoints,
including document creation, retrieval, updates, and error handling.
It verifies both successful operations and error cases.
"""

from __future__ import annotations

import json

import pytest
import sqlalchemy
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.notebook.models.document import Document
from ring.notebook.schemas.document import DocumentCreate, DocumentUpdate
from ring.security import create_access_token
from ring.tests.factories.notebook.document_factory import DocumentFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory
from ring.tests.lib.utils import (
    assert_api_model_not_found,
    assert_pydantic_model_json_dump_equivalent_to_response_dict,
    assert_pydantic_models_json_dump_in_response_dict,
)


class TestDocumentAPI:
    """Test suite for document API endpoints.

    This class contains tests for all document-related API operations,
    including CRUD operations, schema validation, and error handling.
    """

    def test_create_document_schema(self, db_session: Session):
        """Test that DocumentCreate schema works correctly.

        This test verifies that:
        1. DocumentCreate schema accepts valid data
        2. The schema correctly validates required fields
        3. The schema properly handles string content

        Args:
            faker (Faker): Faker instance for generating test data
        """
        group = GroupFactory.create()
        db_session.commit()

        document_data = {
            "name": "Test Document",
            "content": "This is a test document content.",
            "group_api_id": group.api_identifier,
        }
        document = DocumentCreate(**document_data)
        assert document.name == "Test Document"
        assert document.content == "This is a test document content."
        assert document.group_api_id == group.api_identifier

    def test_update_document_schema(self):
        """Test that DocumentUpdate schema works correctly.

        This test verifies that:
        1. DocumentUpdate schema accepts valid data
        2. The schema correctly validates optional fields
        3. The schema properly handles string content

        Args:
            faker (Faker): Faker instance for generating test data
        """
        update_data = {
            "name": "Updated Document Name",
            "content": "Updated content.",
        }
        update = DocumentUpdate(**update_data)
        assert update.name == "Updated Document Name"
        assert update.content == "Updated content."

    def test_document_schemas_optional_fields(self):
        """Test that DocumentUpdate schema allows partial updates.

        This test verifies that:
        1. DocumentUpdate schema allows updating only the name
        2. DocumentUpdate schema allows updating only the content
        3. Unspecified fields remain None
        4. The schema correctly handles partial updates

        Args:
            faker (Faker): Faker instance for generating test data
        """
        update_data = {"name": "Only Name Update"}
        update = DocumentUpdate(**update_data)
        assert update.name == "Only Name Update"
        assert update.content is None

        update_data = {"content": "Only Content Update"}
        update = DocumentUpdate(**update_data)
        assert update.name is None
        assert update.content == "Only Content Update"

    def test_create_document(
        self,
        authenticated_client: TestClient,
        faker: Faker,
        db_session: Session,
    ) -> None:
        """Test creating a new document with valid data.

        This test verifies that:
        1. A document can be created with valid name and content
        2. The response contains the correct document data
        3. The document is properly stored in the database
        4. The response matches the database state

        Args:
            authenticated_client (TestClient): Authenticated test client
            faker (Faker): Faker instance for generating test data
            db_session (Session): Database session
        """

        group = GroupFactory.create()
        db_session.commit()

        name, content = (
            faker.sentence(nb_words=3),
            faker.text(max_nb_chars=500),
        )
        input_data: dict[str, str] = {
            "name": name,
            "content": content,
            "group_api_id": group.api_identifier,
        }
        response = authenticated_client.post(
            "/notebook/documents", json=input_data
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == name
        assert data["content"] == content
        assert data["latest_snapshot_version"] == 0
        # Verify document was created in database
        db_document = db_session.scalar(
            sqlalchemy.select(Document).filter(Document.name == name)
        )
        assert db_document is not None
        assert db_document.name == name
        assert db_document.content.decode("utf-8") == content
        assert db_document.group == group

    def test_create_document_unauthenticated(
        self,
        unauthenticated_client: TestClient,
        faker: Faker,
    ) -> None:
        """Test creating a document when not authenticated.

        This test verifies that:
        1. Creating a document fails when not authenticated
        2. The response contains the correct error message
        3. The response indicates authentication is required

        Args:
            unauthenticated_client (TestClient): Unauthenticated test client
            faker (Faker): Faker instance for generating test data
        """
        input_data: dict[str, str] = {
            "name": faker.sentence(nb_words=3),
            "content": faker.text(max_nb_chars=500),
        }
        response = unauthenticated_client.post(
            "/notebook/documents", json=input_data
        )

        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Not authenticated"

    def test_get_document(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        """Test retrieving a document by its API identifier.

        This test verifies that:
        1. A document can be retrieved by its API identifier
        2. The response contains the correct document data
        3. The response matches the database state
        4. All document fields are included in the response

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
        """
        document = DocumentFactory.create()
        db_session.commit()

        response = authenticated_client.get(
            f"/notebook/documents/{document.api_identifier}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["api_identifier"] == document.api_identifier
        assert data["name"] == document.name
        assert data["content"] == document.content.decode("utf-8")
        assert (
            data["latest_snapshot_version"] == document.latest_snapshot_version
        )

    def test_get_document_not_found(
        self,
        authenticated_client: TestClient,
    ) -> None:
        """Test retrieving a non-existent document.

        This test verifies that:
        1. Retrieving a non-existent document fails
        2. The response contains the correct error message
        3. The response indicates the document was not found

        Args:
            authenticated_client (TestClient): Authenticated test client
        """
        response = authenticated_client.get("/notebook/documents/invalid_id")
        assert response.status_code == 404
        data = response.json()
        assert_api_model_not_found(data, Document, ["invalid_id"])

    def test_get_document_unauthenticated(
        self,
        unauthenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        """Test retrieving a document when not authenticated.

        This test verifies that:
        1. Retrieving a document fails when not authenticated
        2. The response contains the correct error message
        3. The response indicates authentication is required

        Args:
            unauthenticated_client (TestClient): Unauthenticated test client
            db_session (Session): Database session
        """
        document = DocumentFactory.create()
        db_session.commit()

        response = unauthenticated_client.get(
            f"/notebook/documents/{document.api_identifier}"
        )
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Not authenticated"

    def test_update_document_name_only(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        faker: Faker,
    ) -> None:
        """Test updating only the document name.

        This test verifies that:
        1. A document's name can be updated independently
        2. The response contains the updated document data
        3. The document's content remains unchanged
        4. The database state is updated correctly

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
            faker (Faker): Faker instance for generating test data
        """
        document = DocumentFactory.create()
        db_session.commit()

        new_name = faker.sentence(nb_words=3)
        input_data = {"name": new_name}
        response = authenticated_client.put(
            f"/notebook/documents/{document.api_identifier}", json=input_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == new_name
        assert data["content"] == document.content.decode("utf-8")
        assert (
            data["latest_snapshot_version"] == document.latest_snapshot_version
        )

    def test_update_document_content_only(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        faker: Faker,
    ) -> None:
        """Test updating only the document content.

        This test verifies that:
        1. A document's content can be updated independently
        2. The response contains the updated document data
        3. The document's name remains unchanged
        4. The version is incremented when content changes

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
            faker (Faker): Faker instance for generating test data
        """
        document = DocumentFactory.create()
        db_session.commit()

        new_content = faker.text(max_nb_chars=500)
        input_data = {"content": new_content}
        response = authenticated_client.put(
            f"/notebook/documents/{document.api_identifier}", json=input_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == document.name
        assert data["content"] == new_content
        assert (
            data["latest_snapshot_version"] == document.latest_snapshot_version
        )  # No auto-increment

    def test_update_document_both_fields(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        faker: Faker,
    ) -> None:
        """Test updating both document name and content.

        This test verifies that:
        1. Both name and content can be updated simultaneously
        2. The response contains the updated document data
        3. The version is incremented when content changes
        4. The database state is updated correctly

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
            faker (Faker): Faker instance for generating test data
        """
        document = DocumentFactory.create()
        db_session.commit()

        new_name = faker.sentence(nb_words=3)
        new_content = faker.text(max_nb_chars=500)
        input_data = {"name": new_name, "content": new_content}
        response = authenticated_client.put(
            f"/notebook/documents/{document.api_identifier}", json=input_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == new_name
        assert data["content"] == new_content
        assert (
            data["latest_snapshot_version"] == document.latest_snapshot_version
        )  # No auto-increment

    def test_update_document_not_found(
        self,
        authenticated_client: TestClient,
        faker: Faker,
    ) -> None:
        """Test updating a non-existent document.

        This test verifies that:
        1. Updating a non-existent document fails
        2. The response contains the correct error message
        3. The response indicates the document was not found

        Args:
            authenticated_client (TestClient): Authenticated test client
            faker (Faker): Faker instance for generating test data
        """
        input_data = {
            "name": faker.sentence(nb_words=3),
            "content": faker.text(max_nb_chars=500),
        }
        response = authenticated_client.put(
            "/notebook/documents/invalid_id", json=input_data
        )
        assert response.status_code == 404
        data = response.json()
        assert_api_model_not_found(data, Document, ["invalid_id"])

    def test_update_document_unauthenticated(
        self,
        unauthenticated_client: TestClient,
        db_session: Session,
        faker: Faker,
    ) -> None:
        """Test updating a document when not authenticated.

        This test verifies that:
        1. Updating a document fails when not authenticated
        2. The response contains the correct error message
        3. The response indicates authentication is required

        Args:
            unauthenticated_client (TestClient): Unauthenticated test client
            db_session (Session): Database session
            faker (Faker): Faker instance for generating test data
        """
        document = DocumentFactory.create()
        db_session.commit()

        input_data = {
            "name": faker.sentence(nb_words=3),
            "content": faker.text(max_nb_chars=500),
        }
        response = unauthenticated_client.put(
            f"/notebook/documents/{document.api_identifier}", json=input_data
        )
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Not authenticated"

    def test_list_documents(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        """Test listing documents for a group."""
        group = GroupFactory.create()
        documents = [DocumentFactory.create(group=group) for _ in range(3)]
        db_session.commit()
        response = authenticated_client.get(
            f"/notebook/documents/?group_api_id={group.api_identifier}"
        )
        assert response.status_code == 200
        data = response.json()
        print(data)
        assert len(data) == 3
        assert_pydantic_models_json_dump_in_response_dict(documents, data)

    def test_document_websocket_ping_pong(
        self,
        unauthenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        """Application-level ping must get a pong (not be broadcast)."""
        user = UserFactory.create()
        document = DocumentFactory.create()
        db_session.commit()

        token = create_access_token({"sub": user.email})
        with unauthenticated_client.websocket_connect(
            f"/ws/notebook/{document.api_identifier}?token={token}"
        ) as ws:
            ws.send_text(json.dumps({"type": "ping"}))
            assert json.loads(ws.receive_text()) == {"type": "pong"}
