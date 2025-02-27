from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.parties.crud.group_key_value import (
    get_all_values,
    get_value,
    set_value,
)
from ring.parties.models.user_model import User
from ring.tests.factories.parties.group_factory import GroupFactory


class TestGroupKeyValueApi:
    def test_read_all_values(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ):
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
