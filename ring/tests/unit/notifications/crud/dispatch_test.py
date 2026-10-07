"""Tests for inbox persistence on notification sends."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from ring.letters.constants import LetterStatus
from ring.letters.crud import letter as letter_crud
from ring.notifications.crud.dispatch import notify_users
from ring.notifications.crud.inbox import list_inbox_items
from ring.notifications.crud.links import inbox_href
from ring.notifications.models.subscription import Subscription
from ring.parties.crud import group as group_crud
from ring.tasks.crud import task as task_crud
from ring.tasks.models.task_model import TaskType
from ring.tests.factories.letters.letter_factory import (
    LetterFactory,
    UpcomingLetterFactory,
)
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.letters.response_factory import ResponseFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory


class TestInboxHref:
    def test_letter_target(self) -> None:
        assert inbox_href("lttr_abc") == "/loops/lttr_abc"

    def test_group_target(self) -> None:
        assert inbox_href("grp_abc") == "/groups/grp_abc/loops"

    def test_document_target(self) -> None:
        assert inbox_href("dcmnt_abc") == "/documents/dcmnt_abc"

    def test_unknown_target(self) -> None:
        assert inbox_href(None) == "/"
        assert inbox_href("nope") == "/"


class TestNotifyUsers:
    def test_persists_without_subscription(self, db_session: Session) -> None:
        user = UserFactory.create()
        db_session.flush()

        created = notify_users(
            db_session,
            [user, user],
            title="New letter",
            body="Ready",
            target_api_id="lttr_abc",
        )

        assert len(created) == 1
        items = list_inbox_items(db_session, user)
        assert len(items) == 1
        assert items[0].unread is True
        assert items[0].href == "/loops/lttr_abc"

    def test_push_uses_existing_sender_and_group_loops_url(
        self, db_session: Session
    ) -> None:
        user = UserFactory.create()
        db_session.add(
            Subscription.create(
                endpoint="https://push.example/one",
                keys={"p256dh": "key", "auth": "auth"},
                user=user,
            )
        )
        db_session.flush()

        with patch(
            "ring.notifications.crud.dispatch.send_push_notification"
        ) as send_push:
            notify_users(
                db_session,
                [user],
                title="Added to a group",
                body="You were added to Family",
                target_api_id="grp_abc",
            )

        send_push.assert_called_once()
        payload = send_push.call_args.args[1]
        assert payload["title"] == "Added to a group"
        assert payload["url"].endswith("/groups/grp_abc/loops")

    def test_push_failure_still_persists(self, db_session: Session) -> None:
        user = UserFactory.create()
        db_session.add(
            Subscription.create(
                endpoint="https://push.example/two",
                keys={"p256dh": "key", "auth": "auth"},
                user=user,
            )
        )
        db_session.flush()

        with patch(
            "ring.notifications.crud.dispatch.send_push_notification",
            side_effect=RuntimeError("push down"),
        ):
            notify_users(
                db_session,
                [user],
                title="New letter",
                body="Ready",
                target_api_id="lttr_abc",
            )

        assert len(list_inbox_items(db_session, user)) == 1


class TestLetterSentInbox:
    def test_successful_send_creates_inbox_row(
        self, db_session: Session
    ) -> None:
        user = UserFactory.create()
        group = GroupFactory.create(admin=user, members=[user])
        letter = LetterFactory.create(group=group, title="Spring")
        letter.participants = [user]
        db_session.flush()

        with patch(
            "ring.letters.crud.letter.send_email", return_value="ses-id"
        ):
            assert letter_crud.send_letter_email(db_session, letter) is True

        items = list_inbox_items(db_session, user)
        assert len(items) == 1
        assert items[0].href == f"/loops/{letter.api_identifier}"
        assert items[0].target_api_id == letter.api_identifier
        assert letter.status == LetterStatus.SENT

    def test_failed_send_creates_no_inbox_row(
        self, db_session: Session
    ) -> None:
        user = UserFactory.create()
        group = GroupFactory.create(admin=user, members=[user])
        letter = LetterFactory.create(group=group)
        letter.participants = [user]
        db_session.flush()

        with patch("ring.letters.crud.letter.send_email", return_value=None):
            assert letter_crud.send_letter_email(db_session, letter) is False

        assert list_inbox_items(db_session, user) == []
        assert letter.status == LetterStatus.IN_PROGRESS


class TestOtherSends:
    def test_added_member_links_to_group_loops(
        self, db_session: Session
    ) -> None:
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin])
        newcomer = UserFactory.create()
        db_session.flush()

        group_crud.add_member(
            db_session, group.api_identifier, newcomer.api_identifier
        )

        items = list_inbox_items(db_session, newcomer)
        assert len(items) == 1
        assert items[0].href == f"/groups/{group.api_identifier}/loops"
        assert list_inbox_items(db_session, admin) == []

    def test_reminder_persists_when_email_is_not_accepted(
        self, db_session: Session
    ) -> None:
        user = UserFactory.create()
        group = GroupFactory.create(admin=user, members=[user])
        letter = UpcomingLetterFactory.create(
            group=group,
            send_at=datetime.now(tz=UTC) + timedelta(days=20),
        )
        letter.participants = [user]
        db_session.flush()
        reminder = next(
            task
            for task in group.schedule.tasks
            if task.type == TaskType.REMINDER_EMAIL
            and task.execute_at == letter.send_at - timedelta(days=8)
        )

        with patch("ring.tasks.crud.task.send_email", return_value=None):
            task_crud.execute_reminder_email_task(db_session, reminder)

        items = list_inbox_items(db_session, user)
        assert len(items) == 1
        assert items[0].href == f"/loops/{letter.api_identifier}"

    def test_responses_open_persists_when_email_is_not_accepted(
        self, db_session: Session
    ) -> None:
        user = UserFactory.create()
        group = GroupFactory.create(admin=user, members=[user])
        letter = LetterFactory.create(group=group, title="June")
        letter.participants = [user]
        db_session.commit()

        with patch("ring.tasks.crud.task.send_email", return_value=None):
            from ring.async_scheduler.job_registry import JOB_REGISTRY

            JOB_REGISTRY["send_response_open_email"].job_function(
                db_session, letter.id
            )

        items = list_inbox_items(db_session, user)
        assert len(items) == 1
        assert items[0].target_api_id == letter.api_identifier

    def test_waiting_response_notifies_only_non_responders(
        self, db_session: Session
    ) -> None:
        admin = UserFactory.create()
        pending = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin, pending])
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=datetime.now(tz=UTC) - timedelta(minutes=1),
        )
        letter.participants = [admin, pending]
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=admin)
        db_session.commit()

        with patch("ring.tasks.crud.task.send_email", return_value=None):
            from ring.async_scheduler.job_registry import JOB_REGISTRY

            JOB_REGISTRY["send_waiting_response_email"].job_function(
                db_session, letter.id
            )

        assert list_inbox_items(db_session, admin) == []
        items = list_inbox_items(db_session, pending)
        assert len(items) == 1
        assert items[0].href == f"/loops/{letter.api_identifier}"
