"""API tests for the in-app inbox."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.authz.authz import load_and_check
from ring.authz.enforcer import (
    Action,
    build_stateless_enforcer,
    enforce_stateless,
)
from ring.notifications.crud.inbox import list_inbox_items
from ring.tests.factories.notifications.inbox_item_factory import (
    InboxItemFactory,
)
from ring.tests.factories.parties.user_factory import UserFactory


class TestInboxApi:
    def test_list_unread_and_mark_read(
        self,
        authenticated_client: TestClient,
        current_user,
        db_session: Session,
    ) -> None:
        mine = InboxItemFactory.create(
            user=current_user,
            title="New letter",
            body="Ready to read",
            target_api_id="lttr_mine",
        )
        older = InboxItemFactory.create(
            user=current_user,
            title="Older",
            body="Already read",
            target_api_id="lttr_old",
        )
        older.read_at = datetime.now(UTC)
        other = UserFactory.create()
        InboxItemFactory.create(
            user=other,
            title="Not mine",
            body="Hidden",
            target_api_id="grp_other",
        )
        db_session.commit()

        listed = authenticated_client.get("/notifications/inbox")
        assert listed.status_code == 200
        body = listed.json()
        assert len(body) == 2
        assert {item["title"] for item in body} == {"New letter", "Older"}
        letter = next(item for item in body if item["title"] == "New letter")
        assert letter["href"] == "/loops/lttr_mine"
        assert letter["unread"] is True

        unread = authenticated_client.get(
            "/notifications/inbox", params={"unread_only": True}
        )
        assert unread.status_code == 200
        assert len(unread.json()) == 1
        assert unread.json()[0]["api_identifier"] == mine.api_identifier

        count = authenticated_client.get("/notifications/inbox/unread-count")
        assert count.status_code == 200
        assert count.json() == {"unread_count": 1}

        marked = authenticated_client.post(
            f"/notifications/inbox/{mine.api_identifier}/read"
        )
        assert marked.status_code == 200
        assert marked.json()["unread"] is False
        assert marked.json()["read_at"] is not None

        count_after = authenticated_client.get(
            "/notifications/inbox/unread-count"
        )
        assert count_after.json() == {"unread_count": 0}

    def test_mark_all_read(
        self,
        authenticated_client: TestClient,
        current_user,
        db_session: Session,
    ) -> None:
        InboxItemFactory.create(user=current_user, target_api_id="lttr_a")
        InboxItemFactory.create(user=current_user, target_api_id="grp_b")
        db_session.commit()

        response = authenticated_client.post("/notifications/inbox/read-all")
        assert response.status_code == 200
        assert (
            list_inbox_items(db_session, current_user, unread_only=True) == []
        )
        group_item = next(
            item
            for item in list_inbox_items(db_session, current_user)
            if item.target_api_id == "grp_b"
        )
        assert group_item.href == "/groups/grp_b/loops"

    def test_other_user_cannot_mark_read(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        other = UserFactory.create()
        item = InboxItemFactory.create(user=other)
        db_session.commit()

        response = authenticated_client.post(
            f"/notifications/inbox/{item.api_identifier}/read"
        )
        assert response.status_code == 403

    def test_missing_id_is_forbidden(
        self, authenticated_client: TestClient
    ) -> None:
        response = authenticated_client.post(
            "/notifications/inbox/inbx_missing/read"
        )
        assert response.status_code == 403

    def test_user_with_no_groups_can_mark_read(
        self,
        db_session: Session,
        get_client_for_user,
    ) -> None:
        user = UserFactory.create()
        item = InboxItemFactory.create(user=user, target_api_id="lttr_solo")
        db_session.commit()
        assert user.groups == []

        client = get_client_for_user(user)
        response = client.post(
            f"/notifications/inbox/{item.api_identifier}/read"
        )
        assert response.status_code == 200
        assert response.json()["unread"] is False

    def test_full_enforcer_does_not_load_inbox_rows(
        self,
        db_session: Session,
    ) -> None:
        user = UserFactory.create()
        item = InboxItemFactory.create(user=user)
        db_session.commit()

        full = build_stateless_enforcer(db_session, user.api_identifier)
        assert (
            enforce_stateless(
                db_session,
                user.api_identifier,
                item.api_identifier,
                Action.WRITE,
                full,
            )
            is False
        )
        loaded = load_and_check(
            db_session, user, Action.WRITE, item.api_identifier
        )
        assert loaded.api_identifier == item.api_identifier
