"""Tests for the group key-value API endpoints.

This module contains tests for all group key-value related API endpoints,
including reading, setting, updating, and deleting key-value pairs for groups.
It verifies both successful operations and error cases.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.letters.send_threshold import APP_CONTROLLED_GROUP_KEYS
from ring.parties.crud.group_key_value import (
    get_all_values,
    get_value,
    set_value,
)
from ring.parties.models.user_model import User
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory


class TestGroupKeyValueApi:
    """Test suite for group key-value API endpoints.

    This class contains tests for all group key-value related API operations,
    including CRUD operations and bulk updates.
    """

    def test_read_all_values(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ):
        """Test reading all key-value pairs for a group.

        This test verifies that:
        1. All key-value pairs can be retrieved for a group
        2. The response contains the correct key-value data
        3. The data matches what was previously set

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
            current_user (User): Currently authenticated user
        """
        group = GroupFactory.create(admin=current_user)
        db_session.add(group)
        db_session.flush()
        set_value(db_session, group, "test_key", "test_value")
        db_session.commit()
        response = authenticated_client.get(
            f"/parties/group/{group.api_identifier}/key-value"
        )
        assert response.status_code == 200
        assert response.json() == {"key_values": {"test_key": "test_value"}}

    def test_read_value(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ):
        """Test reading a specific key-value pair for a group.

        This test verifies that:
        1. A specific key-value pair can be retrieved
        2. The response contains the correct key and value
        3. The data matches what was previously set

        Args:
            authenticated_client (TestClient): Authenticated test client
            db_session (Session): Database session
            current_user (User): Currently authenticated user
        """
        group = GroupFactory.create(admin=current_user)
        db_session.add(group)
        db_session.flush()
        set_value(db_session, group, "test_key", "test_value")
        db_session.commit()
        response = authenticated_client.get(
            f"/parties/group/{group.api_identifier}/key-value/test_key"
        )
        assert response.status_code == 200
        assert response.json() == {"key": "test_key", "value": "test_value"}

    def test_update_group_key_value(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ):
        """Test updating a key-value pair for a group.

        This test verifies that:
        1. A key-value pair can be set initially
        2. The same key can be updated with a new value
        3. The response contains the correct updated data
        4. The database reflects the changes

        Args:
            authenticated_client (TestClient): Authenticated test client
            current_user (User): Currently authenticated user
            db_session (Session): Database session
        """
        group = GroupFactory.create(admin=current_user)
        db_session.add(group)
        db_session.commit()

        response = authenticated_client.post(
            f"/parties/group/{group.api_identifier}/key-value:update",
            json={
                "key": "test_key",
                "value": "test_value",
                "operation": "set",
            },
        )
        assert response.status_code == 200
        assert response.json() == {"key": "test_key", "value": "test_value"}

        assert get_all_values(db_session, group) == {"test_key": "test_value"}

        response = authenticated_client.post(
            f"/parties/group/{group.api_identifier}/key-value:update",
            json={
                "key": "test_key",
                "value": "new_value",
                "operation": "set",
            },
        )
        assert response.status_code == 200
        assert response.json() == {"key": "test_key", "value": "new_value"}
        assert get_all_values(db_session, group) == {"test_key": "new_value"}

    def test_delete_group_key_value(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ):
        """Test deleting a key-value pair from a group.

        This test verifies that:
        1. An existing key-value pair can be deleted
        2. The response indicates successful deletion
        3. The key-value pair is removed from the database

        Args:
            authenticated_client (TestClient): Authenticated test client
            current_user (User): Currently authenticated user
            db_session (Session): Database session
        """
        group = GroupFactory.create(admin=current_user)
        db_session.add(group)
        db_session.flush()
        set_value(db_session, group, "test_key", "test_value")
        db_session.commit()
        response = authenticated_client.post(
            f"/parties/group/{group.api_identifier}/key-value:update",
            json={
                "key": "test_key",
                "value": "test_value",
                "operation": "delete",
            },
        )
        assert response.status_code == 200
        assert response.json() == {"key": "test_key", "value": None}
        assert get_all_values(db_session, group) == {}

    def test_delete_non_existent_group_key_value(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ):
        """Test deleting a non-existent key-value pair.

        This test verifies that:
        1. Deleting a non-existent key-value pair succeeds
        2. The response indicates successful deletion
        3. The database state remains unchanged

        Args:
            authenticated_client (TestClient): Authenticated test client
            current_user (User): Currently authenticated user
            db_session (Session): Database session
        """
        group = GroupFactory.create(admin=current_user)
        db_session.add(group)
        db_session.commit()
        response = authenticated_client.post(
            f"/parties/group/{group.api_identifier}/key-value:update",
            json={
                "key": "test_key",
                "value": "test_value",
                "operation": "delete",
            },
        )
        assert response.status_code == 200
        assert response.json() == {"key": "test_key", "value": None}
        assert get_all_values(db_session, group) == {}

    def test_update_invalid_operation(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ):
        """Test updating with an invalid operation.

        This test verifies that:
        1. Using an invalid operation fails
        2. The response contains the correct error message
        3. The database state remains unchanged

        Args:
            authenticated_client (TestClient): Authenticated test client
            current_user (User): Currently authenticated user
            db_session (Session): Database session
        """
        group = GroupFactory.create(admin=current_user)
        db_session.add(group)
        db_session.flush()
        set_value(db_session, group, "test_key", "test_value")
        db_session.commit()
        response = authenticated_client.post(
            f"/parties/group/{group.api_identifier}/key-value:update",
            json={
                "key": "test_key",
                "value": "new_value",
                "operation": "invalid_operation",
            },
        )
        assert response.status_code == 422
        data = response.json()
        assert data["detail"][0]["msg"] == "Input should be 'set' or 'delete'"

    def test_bulk_update(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ):
        """Test performing bulk updates on key-value pairs.

        This test verifies that:
        1. Multiple key-value operations can be performed in one request
        2. The response contains the correct updated data
        3. The database reflects all changes correctly

        Args:
            authenticated_client (TestClient): Authenticated test client
            current_user (User): Currently authenticated user
            db_session (Session): Database session
        """
        group = GroupFactory.create(admin=current_user)
        db_session.add(group)
        db_session.flush()
        set_value(db_session, group, "test_key", "test_value")
        db_session.commit()
        response = authenticated_client.post(
            f"/parties/group/{group.api_identifier}/key-value:bulk-update",
            json={
                "updates": [
                    {
                        "key": "new_key",
                        "value": "test_value",
                        "operation": "set",
                    },
                    {
                        "key": "test_key",
                        "operation": "delete",
                    },
                ]
            },
        )
        assert response.status_code == 200
        assert response.json() == {
            "key_values": {
                "new_key": "test_value",
            }
        }
        assert get_all_values(db_session, group) == {
            "new_key": "test_value",
        }

    def test_put_keeps_keys_absent_from_the_body(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ):
        """A full-replace body must not delete keys the caller did not send."""
        group = GroupFactory.create(admin=current_user)
        db_session.add(group)
        db_session.flush()
        set_value(db_session, group, "theme", "dark")
        set_value(db_session, group, "note", "keep")
        db_session.commit()

        response = authenticated_client.put(
            f"/parties/group/{group.api_identifier}/key-value",
            json={"key_values": {"theme": "light"}},
        )

        assert response.status_code == 200
        assert response.json()["key_values"] == {
            "theme": "light",
            "note": "keep",
        }
        assert get_all_values(db_session, group) == {
            "theme": "light",
            "note": "keep",
        }

        empty = authenticated_client.put(
            f"/parties/group/{group.api_identifier}/key-value",
            json={"key_values": {}},
        )
        assert empty.status_code == 200
        assert get_all_values(db_session, group) == {
            "theme": "light",
            "note": "keep",
        }

    def test_store_reads_hide_app_settings(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ):
        """Leftover letter-send keys are not part of the store response."""
        group = GroupFactory.create(admin=current_user)
        group.key_values.set_value("letter_send_min_responders", 9)
        group.key_values.set_value("letter_send_min_responder_ratio", 0.1)
        group.key_values.set_value("theme", "dark")
        group.min_responders = 4
        group.min_responder_ratio = 0.5
        db_session.commit()

        listed = authenticated_client.get(
            f"/parties/group/{group.api_identifier}/key-value"
        )
        assert listed.status_code == 200
        assert listed.json() == {"key_values": {"theme": "dark"}}

        one = authenticated_client.get(
            f"/parties/group/{group.api_identifier}/key-value/"
            "letter_send_min_responders"
        )
        assert one.status_code == 200
        assert one.json() == {
            "key": "letter_send_min_responders",
            "value": None,
        }

        group_response = authenticated_client.get(
            f"/parties/group/{group.api_identifier}"
        )
        assert group_response.status_code == 200
        assert group_response.json()["min_responders"] == 4
        assert group_response.json()["min_responder_ratio"] == 0.5

    def test_member_cannot_write_app_settings_through_the_store(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ):
        """Non-admins cannot change letter-send settings from any store route."""
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin, current_user])
        group.min_responders = 2
        group.min_responder_ratio = 0.5
        db_session.commit()

        for key in APP_CONTROLLED_GROUP_KEYS:
            single = authenticated_client.post(
                f"/parties/group/{group.api_identifier}/key-value:update",
                json={"key": key, "value": 1, "operation": "set"},
            )
            assert single.status_code == 400

            deleted = authenticated_client.post(
                f"/parties/group/{group.api_identifier}/key-value:update",
                json={"key": key, "operation": "delete"},
            )
            assert deleted.status_code == 400

            bulk = authenticated_client.post(
                f"/parties/group/{group.api_identifier}/key-value:bulk-update",
                json={
                    "updates": [
                        {
                            "key": "theme",
                            "value": "dark",
                            "operation": "set",
                        },
                        {"key": key, "value": 1, "operation": "set"},
                    ]
                },
            )
            assert bulk.status_code == 400

            replaced = authenticated_client.put(
                f"/parties/group/{group.api_identifier}/key-value",
                json={"key_values": {key: 1, "theme": "dark"}},
            )
            assert replaced.status_code == 400

        db_session.refresh(group)
        assert group.min_responders == 2
        assert group.min_responder_ratio == 0.5
        assert get_all_values(db_session, group) == {}

        allowed = authenticated_client.post(
            f"/parties/group/{group.api_identifier}/key-value:update",
            json={"key": "theme", "value": "dark", "operation": "set"},
        )
        assert allowed.status_code == 200
        assert get_value(db_session, group, "theme") == "dark"

    def test_admin_cannot_write_app_settings_through_the_store(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ):
        """The group admin changes letter-send settings on the group route."""
        group = GroupFactory.create(admin=current_user)
        group.min_responders = 2
        db_session.commit()

        response = authenticated_client.post(
            f"/parties/group/{group.api_identifier}/key-value:update",
            json={
                "key": "letter_send_min_responders",
                "value": 9,
                "operation": "set",
            },
        )
        assert response.status_code == 400
        db_session.refresh(group)
        assert group.min_responders == 2
