"""Authz coverage for schedule read.

Any authenticated user could previously fetch another group's schedule by
API id. These tests pin membership gating via load_and_check.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.parties.models.user_model import User
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory


class TestScheduleAuthz:
    def test_non_member_cannot_read_schedule(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        group = GroupFactory.create()
        db_session.commit()

        response = authenticated_client.get(
            f"/schedule/schedule/{group.api_identifier}"
        )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Not authorized to access this resource"
        )

    def test_member_can_read_schedule(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin, current_user])
        db_session.commit()

        response = authenticated_client.get(
            f"/schedule/schedule/{group.api_identifier}"
        )

        assert response.status_code == 200
        body = response.json()
        assert body["group"]["api_identifier"] == group.api_identifier
        assert "tasks" in body

    def test_missing_group_looks_forbidden(
        self,
        authenticated_client: TestClient,
    ) -> None:
        response = authenticated_client.get(
            "/schedule/schedule/grp_does-not-exist"
        )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Not authorized to access this resource"
        )
