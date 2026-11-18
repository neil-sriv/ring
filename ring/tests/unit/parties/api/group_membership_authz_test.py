"""Authz coverage for group membership-gated endpoints.

Manual ``current_user not in members`` checks returned 404 and skipped the
shared Casbin path. These tests pin ``load_and_check`` so missing groups and
non-members both look like forbidden access.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.parties.crud.group_key_value import set_value
from ring.parties.models.user_model import User
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory

FORBIDDEN = {"detail": "Not authorized to access this resource"}


class TestGroupMembershipAuthz:
    def test_non_member_cannot_read_group(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        group = GroupFactory.create()
        db_session.commit()

        response = authenticated_client.get(
            f"/parties/group/{group.api_identifier}"
        )

        assert response.status_code == 403
        assert response.json() == FORBIDDEN

    def test_member_can_read_group(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin, current_user])
        db_session.commit()

        response = authenticated_client.get(
            f"/parties/group/{group.api_identifier}"
        )

        assert response.status_code == 200
        assert response.json()["api_identifier"] == group.api_identifier

    def test_missing_group_looks_forbidden(
        self,
        authenticated_client: TestClient,
    ) -> None:
        response = authenticated_client.get(
            "/parties/group/grp_does-not-exist"
        )

        assert response.status_code == 403
        assert response.json() == FORBIDDEN

    def test_non_member_cannot_update_group(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        group = GroupFactory.create()
        db_session.commit()

        response = authenticated_client.patch(
            f"/parties/group/{group.api_identifier}",
            json={"name": "Hijacked"},
        )

        assert response.status_code == 403
        assert response.json() == FORBIDDEN

    def test_non_admin_member_cannot_update_group(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin, current_user])
        db_session.commit()

        response = authenticated_client.patch(
            f"/parties/group/{group.api_identifier}",
            json={"name": "Hijacked"},
        )

        assert response.status_code == 403
        assert response.json() == {
            "detail": "Only the group admin can update the group information"
        }

    def test_non_member_cannot_remove_member(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        admin = UserFactory.create()
        member = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin, member])
        db_session.commit()

        response = authenticated_client.post(
            f"/parties/group/{group.api_identifier}:remove_member/"
            f"{member.api_identifier}"
        )

        assert response.status_code == 403
        assert response.json() == FORBIDDEN

    def test_non_member_cannot_replace_default_questions(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        group = GroupFactory.create()
        db_session.commit()

        response = authenticated_client.post(
            f"/parties/group/{group.api_identifier}:replace_default_questions",
            json={"questions": ["What is new?"]},
        )

        assert response.status_code == 403
        assert response.json() == FORBIDDEN


class TestGroupKeyValueAuthz:
    def test_non_member_cannot_read_key_values(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        group = GroupFactory.create()
        db_session.flush()
        set_value(db_session, group, "secret", "value")
        db_session.commit()

        response = authenticated_client.get(
            f"/parties/group/{group.api_identifier}/key-value"
        )

        assert response.status_code == 403
        assert response.json() == FORBIDDEN

    def test_member_can_read_and_update_key_values(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin, current_user])
        db_session.commit()

        read_response = authenticated_client.get(
            f"/parties/group/{group.api_identifier}/key-value"
        )
        assert read_response.status_code == 200
        assert read_response.json() == {"key_values": {}}

        update_response = authenticated_client.post(
            f"/parties/group/{group.api_identifier}/key-value:update",
            json={
                "key": "theme",
                "value": "dark",
                "operation": "set",
            },
        )
        assert update_response.status_code == 200
        assert update_response.json() == {"key": "theme", "value": "dark"}

    def test_non_member_cannot_update_key_values(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        group = GroupFactory.create()
        db_session.commit()

        response = authenticated_client.post(
            f"/parties/group/{group.api_identifier}/key-value:update",
            json={
                "key": "theme",
                "value": "dark",
                "operation": "set",
            },
        )

        assert response.status_code == 403
        assert response.json() == FORBIDDEN

    def test_non_member_cannot_bulk_update_or_replace_key_values(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        group = GroupFactory.create()
        db_session.commit()

        bulk_response = authenticated_client.post(
            f"/parties/group/{group.api_identifier}/key-value:bulk-update",
            json={
                "updates": [
                    {
                        "key": "theme",
                        "value": "dark",
                        "operation": "set",
                    }
                ]
            },
        )
        assert bulk_response.status_code == 403
        assert bulk_response.json() == FORBIDDEN

        replace_response = authenticated_client.put(
            f"/parties/group/{group.api_identifier}/key-value",
            json={"key_values": {"theme": "dark"}},
        )
        assert replace_response.status_code == 403
        assert replace_response.json() == FORBIDDEN

    def test_missing_group_key_value_looks_forbidden(
        self,
        authenticated_client: TestClient,
    ) -> None:
        response = authenticated_client.get(
            "/parties/group/grp_does-not-exist/key-value"
        )

        assert response.status_code == 403
        assert response.json() == FORBIDDEN
