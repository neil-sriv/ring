"""Authz coverage for group member-add / invite endpoints.

The UI already hides Add Members from non-admins. These tests pin the matching
API gates so membership mutations stay admin-only even when a caller hits the
endpoints directly.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.parties.models.user_model import User
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory


class TestGroupMemberAuthz:
    def test_non_member_cannot_add_member(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        group = GroupFactory.create()
        new_user = UserFactory.create()
        db_session.commit()

        response = authenticated_client.post(
            f"/parties/group/{group.api_identifier}:add_member/{new_user.api_identifier}"
        )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Not authorized to access this resource"
        )
        assert new_user not in group.members

    def test_non_admin_member_cannot_add_member(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin, current_user])
        new_user = UserFactory.create()
        db_session.commit()

        response = authenticated_client.post(
            f"/parties/group/{group.api_identifier}:add_member/{new_user.api_identifier}"
        )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Only the group admin can add members"
        )
        assert new_user not in group.members

    def test_non_admin_member_cannot_add_members(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin, current_user])
        new_user = UserFactory.create()
        db_session.commit()

        response = authenticated_client.post(
            f"/parties/group/{group.api_identifier}:add_members",
            json={"member_emails": [new_user.email]},
        )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Only the group admin can add members"
        )
        assert new_user not in group.members

    def test_admin_can_add_members(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        group = GroupFactory.create(admin=current_user)
        new_user = UserFactory.create()
        db_session.commit()

        response = authenticated_client.post(
            f"/parties/group/{group.api_identifier}:add_members",
            json={"member_emails": [new_user.email]},
        )

        assert response.status_code == 200
        assert new_user in group.members

    def test_non_member_cannot_create_invite(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        group = GroupFactory.create()
        db_session.commit()

        response = authenticated_client.post(
            "/invites/",
            json={
                "email": "outsider-invite@example.com",
                "group_api_id": group.api_identifier,
            },
        )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Not authorized to access this resource"
        )

    def test_non_admin_member_cannot_create_invite(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin, current_user])
        db_session.commit()

        response = authenticated_client.post(
            "/invites/",
            json={
                "email": "member-invite@example.com",
                "group_api_id": group.api_identifier,
            },
        )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Only the group admin can create invites"
        )

    def test_admin_can_create_invite(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        group = GroupFactory.create(admin=current_user)
        db_session.commit()

        response = authenticated_client.post(
            "/invites/",
            json={
                "email": "admin-invite@example.com",
                "group_api_id": group.api_identifier,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin-invite@example.com"
        assert data["group"]["api_identifier"] == group.api_identifier
