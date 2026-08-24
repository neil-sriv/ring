"""Tests for product-event notification helpers and their wiring.

This module tests the per-event notification helpers (copy, recipients,
targets) and verifies the email task flows fan out in-app notifications.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from sqlalchemy import select
from sqlalchemy.orm import Session

from ring.async_scheduler.job_registry import JOB_REGISTRY
from ring.letters.constants import LetterStatus
from ring.notifications.constants import NotificationType
from ring.notifications.crud import events
from ring.notifications.crud.notification import list_notifications
from ring.parties.models.user_model import User
from ring.tasks.crud import task as task_crud
from ring.tasks.models.task_model import Task, TaskType
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.letters.response_factory import ResponseFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory
from ring.tests.lib.utils import run_scheduled_jobs_inline


def _group_with_members(
    member_count: int = 3,
) -> tuple[User, list[User], object]:
    admin = UserFactory.create()
    members = [admin] + [UserFactory.create() for _ in range(member_count)]
    group = GroupFactory.create(admin=admin, members=members)
    return admin, members, group


class TestLetterEventHelpers:
    """Test suite for letter lifecycle notification helpers."""

    def test_notify_letter_sent_notifies_all_participants(
        self, db_session: Session
    ) -> None:
        _, members, group = _group_with_members()
        letter = LetterFactory.create(group=group)
        db_session.commit()

        created = events.notify_letter_sent(db_session, letter)
        db_session.commit()

        assert len(created) == len(members)
        for member in members:
            notifications = list_notifications(db_session, member)
            assert len(notifications) == 1
            notification = notifications[0]
            assert notification.type == NotificationType.LETTER_SENT
            assert group.name in notification.title
            assert f"#{letter.number}" in notification.body
            assert notification.target_api_id == letter.api_identifier

    def test_notify_responses_open_notifies_all_participants(
        self, db_session: Session
    ) -> None:
        _, members, group = _group_with_members()
        letter = LetterFactory.create(group=group)
        db_session.commit()

        created = events.notify_responses_open(db_session, letter)
        db_session.commit()

        assert len(created) == len(members)
        assert all(n.type == NotificationType.RESPONSES_OPEN for n in created)
        assert all("open for responses" in n.title for n in created)

    def test_notify_letter_reminder_upcoming_mentions_questions(
        self, db_session: Session
    ) -> None:
        _, members, group = _group_with_members()
        letter = LetterFactory.create(
            group=group, status=LetterStatus.UPCOMING
        )
        db_session.commit()

        created = events.notify_letter_reminder(db_session, letter)
        db_session.commit()

        assert len(created) == len(members)
        assert all(n.type == NotificationType.LETTER_REMINDER for n in created)
        assert all("add questions" in n.title for n in created)

    def test_notify_letter_reminder_in_progress_mentions_respond(
        self, db_session: Session
    ) -> None:
        _, _, group = _group_with_members()
        letter = LetterFactory.create(
            group=group, status=LetterStatus.IN_PROGRESS
        )
        db_session.commit()

        created = events.notify_letter_reminder(db_session, letter)
        db_session.commit()

        assert all("respond" in n.title for n in created)

    def test_notify_awaiting_response_targets_only_non_responders(
        self, db_session: Session
    ) -> None:
        _, members, group = _group_with_members()
        letter = LetterFactory.create(
            group=group, status=LetterStatus.IN_PROGRESS
        )
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=members[0])
        db_session.commit()

        created = events.notify_awaiting_response(db_session, letter)
        db_session.commit()

        assert len(created) == len(members) - 1
        assert list_notifications(db_session, members[0]) == []
        for member in members[1:]:
            notifications = list_notifications(db_session, member)
            assert len(notifications) == 1
            assert notifications[0].type == NotificationType.AWAITING_RESPONSE

    def test_notify_awaiting_response_noops_when_everyone_answered(
        self, db_session: Session
    ) -> None:
        _, members, group = _group_with_members()
        letter = LetterFactory.create(
            group=group, status=LetterStatus.IN_PROGRESS
        )
        question = QuestionFactory.create(letter=letter)
        for member in members:
            ResponseFactory.create(question=question, participant=member)
        db_session.commit()

        assert events.notify_awaiting_response(db_session, letter) == []


class TestGroupEventHelpers:
    """Test suite for group membership notification helpers."""

    def test_notify_added_to_group_excludes_actor(
        self, db_session: Session
    ) -> None:
        admin, _, group = _group_with_members(member_count=0)
        new_user = UserFactory.create()
        db_session.commit()

        created = events.notify_added_to_group(
            db_session, group, [new_user, admin], admin
        )
        db_session.commit()

        assert len(created) == 1
        notifications = list_notifications(db_session, new_user)
        assert len(notifications) == 1
        notification = notifications[0]
        assert notification.type == NotificationType.ADDED_TO_GROUP
        assert group.name in notification.title
        assert (admin.name or admin.email) in notification.body
        assert notification.target_api_id == group.api_identifier
        assert list_notifications(db_session, admin) == []

    def test_notify_added_to_group_noops_for_empty_list(
        self, db_session: Session
    ) -> None:
        admin, _, group = _group_with_members(member_count=0)
        db_session.commit()

        assert events.notify_added_to_group(db_session, group, [], admin) == []


class TestMemberJoinedHelper:
    """Test suite for the member-joined notification helper."""

    def test_notifies_existing_members_only(self, db_session: Session) -> None:
        admin, members, group = _group_with_members(member_count=2)
        new_user = UserFactory.create()
        group.members.append(new_user)
        db_session.commit()

        created = events.notify_member_joined(
            db_session, group, [new_user], actor=admin
        )
        db_session.commit()

        # Existing members minus the actor; never the new member.
        assert len(created) == 2
        assert list_notifications(db_session, new_user) == []
        assert list_notifications(db_session, admin) == []
        for member in members[1:]:
            notifications = list_notifications(db_session, member)
            assert [n.type for n in notifications] == [
                NotificationType.MEMBER_JOINED
            ]
            assert group.name in notifications[0].title
            assert notifications[0].target_api_id == group.api_identifier

    def test_joined_name_formatting(self, db_session: Session) -> None:
        admin, _, group = _group_with_members(member_count=1)
        new_users = [
            UserFactory.create(name=name)
            for name in ["Ada", "Bob", "Cam", "Dot"]
        ]
        group.members.extend(new_users)
        db_session.commit()

        created = events.notify_member_joined(db_session, group, new_users)
        db_session.commit()

        assert created
        assert "Ada, Bob, and 2 more" in created[0].title

    def test_noops_without_new_members(self, db_session: Session) -> None:
        admin, _, group = _group_with_members()
        db_session.commit()
        assert events.notify_member_joined(db_session, group, []) == []


class TestNewQuestionHelper:
    """Test suite for the new-question notification helper."""

    def test_notifies_participants_except_asker_and_author(
        self, db_session: Session
    ) -> None:
        _, members, group = _group_with_members()
        letter = LetterFactory.create(
            group=group, status=LetterStatus.IN_PROGRESS
        )
        db_session.commit()

        created = events.notify_new_question(
            db_session,
            letter,
            "What was the highlight of your month?",
            asked_by=members[0],
            author=members[1],
        )
        db_session.commit()

        assert len(created) == len(members) - 2
        assert list_notifications(db_session, members[0]) == []
        assert list_notifications(db_session, members[1]) == []
        notifications = list_notifications(db_session, members[2])
        assert [n.type for n in notifications] == [
            NotificationType.NEW_QUESTION
        ]
        assert "highlight of your month" in notifications[0].body
        assert (members[1].name or members[1].email) in notifications[0].body
        assert notifications[0].target_api_id == letter.api_identifier

    def test_noops_for_sent_letter(self, db_session: Session) -> None:
        _, members, group = _group_with_members()
        letter = LetterFactory.create(group=group, status=LetterStatus.SENT)
        db_session.commit()

        assert (
            events.notify_new_question(
                db_session, letter, "Too late?", asked_by=members[0]
            )
            == []
        )

    def test_long_question_text_is_truncated(
        self, db_session: Session
    ) -> None:
        _, members, group = _group_with_members()
        letter = LetterFactory.create(
            group=group, status=LetterStatus.IN_PROGRESS
        )
        db_session.commit()

        created = events.notify_new_question(
            db_session,
            letter,
            "x" * 300,
            asked_by=members[0],
        )
        db_session.commit()

        assert created
        assert "…" in created[0].body
        assert len(created[0].body) < 200


class TestNewResponseHelper:
    """Test suite for the new-response notification helper."""

    def test_notifies_question_author(self, db_session: Session) -> None:
        _, members, group = _group_with_members()
        letter = LetterFactory.create(
            group=group, status=LetterStatus.IN_PROGRESS
        )
        question = QuestionFactory.create(letter=letter, author=members[0])
        db_session.commit()

        created = events.notify_new_response(
            db_session, question, responder=members[1]
        )
        db_session.commit()

        assert len(created) == 1
        notifications = list_notifications(db_session, members[0])
        assert [n.type for n in notifications] == [
            NotificationType.NEW_RESPONSE
        ]
        assert (members[1].name or members[1].email) in notifications[0].title
        assert notifications[0].target_api_id == letter.api_identifier
        # Nobody else hears about individual answers.
        assert list_notifications(db_session, members[2]) == []

    def test_noops_for_own_answer_or_authorless_question(
        self, db_session: Session
    ) -> None:
        _, members, group = _group_with_members()
        letter = LetterFactory.create(
            group=group, status=LetterStatus.IN_PROGRESS
        )
        authored = QuestionFactory.create(letter=letter, author=members[0])
        authorless = QuestionFactory.create(letter=letter, author=None)
        db_session.commit()

        assert (
            events.notify_new_response(
                db_session, authored, responder=members[0]
            )
            == []
        )
        assert (
            events.notify_new_response(
                db_session, authorless, responder=members[1]
            )
            == []
        )


class TestEmailTaskNotificationWiring:
    """The email task flows fan out matching in-app notifications."""

    def test_send_email_task_creates_letter_sent_notifications(
        self, db_session: Session
    ) -> None:
        _, members, group = _group_with_members()
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=datetime.now(tz=UTC) + timedelta(days=1),
        )
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=members[0])
        ResponseFactory.create(question=question, participant=members[1])
        db_session.commit()

        send_task = db_session.scalars(
            select(Task).where(
                Task.schedule_id == group.schedule.id,
                Task.type == TaskType.SEND_EMAIL,
                Task.arguments == {"letter_id": letter.id},
            )
        ).one()

        with (
            run_scheduled_jobs_inline(db_session),
            patch(
                "ring.tasks.crud.task.send_email", return_value="message-id"
            ),
        ):
            task_crud.execute_send_email_task(db_session, send_task)

        for member in members:
            notifications = list_notifications(db_session, member)
            assert [n.type for n in notifications] == [
                NotificationType.LETTER_SENT
            ]

    def test_deferred_send_creates_awaiting_response_notifications(
        self, db_session: Session
    ) -> None:
        _, members, group = _group_with_members()
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=datetime.now(tz=UTC) - timedelta(minutes=1),
        )
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=members[0])
        db_session.commit()

        send_task = db_session.scalars(
            select(Task).where(
                Task.schedule_id == group.schedule.id,
                Task.type == TaskType.SEND_EMAIL,
                Task.arguments == {"letter_id": letter.id},
            )
        ).one()

        with (
            run_scheduled_jobs_inline(db_session),
            patch(
                "ring.tasks.crud.task.send_email", return_value="message-id"
            ),
        ):
            task_crud.execute_send_email_task(db_session, send_task)

        # The responder is not nagged; non-responders each get exactly one
        # awaiting-response notification and no letter-sent notification.
        assert list_notifications(db_session, members[0]) == []
        for member in members[1:]:
            notifications = list_notifications(db_session, member)
            assert [n.type for n in notifications] == [
                NotificationType.AWAITING_RESPONSE
            ]

    def test_reminder_email_task_creates_reminder_notifications(
        self, db_session: Session
    ) -> None:
        _, members, group = _group_with_members()
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=datetime.now(tz=UTC) + timedelta(days=2),
        )
        db_session.commit()

        reminder_task = db_session.scalars(
            select(Task)
            .where(
                Task.schedule_id == group.schedule.id,
                Task.type == TaskType.REMINDER_EMAIL,
            )
            .order_by(Task.execute_at.desc())
            .limit(1)
        ).one()

        with (
            run_scheduled_jobs_inline(db_session),
            patch(
                "ring.tasks.crud.task.send_email", return_value="message-id"
            ),
        ):
            task_crud.execute_reminder_email_task(
                db_session,
                reminder_task,
                letter_status=LetterStatus.IN_PROGRESS,
                letter_id=letter.id,
            )

        for member in members:
            notifications = list_notifications(db_session, member)
            assert [n.type for n in notifications] == [
                NotificationType.LETTER_REMINDER
            ]

    def test_response_open_email_creates_responses_open_notifications(
        self, db_session: Session
    ) -> None:
        _, members, group = _group_with_members()
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=datetime.now(tz=UTC) + timedelta(days=1),
        )
        db_session.commit()

        with patch(
            "ring.tasks.crud.task.send_email", return_value="message-id"
        ):
            JOB_REGISTRY["send_response_open_email"].job_function(
                db_session, letter.id
            )

        for member in members:
            notifications = list_notifications(db_session, member)
            assert [n.type for n in notifications] == [
                NotificationType.RESPONSES_OPEN
            ]
