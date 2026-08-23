"""Tests for task CRUD execution behavior."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from sqlalchemy import select
from sqlalchemy.orm import Session

from ring.letters.constants import LetterStatus
from ring.letters.crud import letter as letter_crud
from ring.letters.send_threshold import (
    GROUP_SETTING_MIN_RESPONDER_RATIO_KEY,
    GROUP_SETTING_MIN_RESPONDERS_KEY,
    LETTER_SEND_DEFERRAL_DAYS,
    defer_letter_send,
    defer_letter_send_if_below_threshold,
)
from ring.tasks.crud import task as task_crud
from ring.tasks.models.task_model import Task, TaskStatus, TaskType
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.letters.response_factory import ResponseFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory
from ring.tests.lib.utils import (
    email_draft_recipients,
    is_waiting_response_email,
    run_scheduled_jobs_inline,
)


class TestTaskCrud:
    """Test suite for task execution logic."""

    def test_execute_send_email_task_defers_when_responders_below_threshold(
        self, db_session: Session
    ) -> None:
        """Defer send by one day and email only people who have not answered."""
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        send_at = datetime.now(tz=UTC) - timedelta(minutes=1)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=send_at,
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
        send_task.status = TaskStatus.IN_PROGRESS
        db_session.commit()

        with (
            run_scheduled_jobs_inline(db_session),
            patch(
                "ring.tasks.crud.task.send_email", return_value="message-id"
            ) as mock_send_email,
        ):
            task_crud.execute_send_email_task(db_session, send_task)

        mock_send_email.assert_called_once()
        assert is_waiting_response_email(mock_send_email)
        recipients = email_draft_recipients(mock_send_email)
        assert set(recipients) == {member.email for member in members[1:]}
        assert members[0].email not in recipients

        db_session.refresh(letter)

        expected_send_at = send_at + timedelta(days=LETTER_SEND_DEFERRAL_DAYS)
        assert letter.send_at == expected_send_at
        assert letter.status == LetterStatus.IN_PROGRESS

        rescheduled_send_task = db_session.scalars(
            select(Task).where(
                Task.schedule_id == group.schedule.id,
                Task.type == TaskType.SEND_EMAIL,
                Task.status == TaskStatus.PENDING,
                Task.arguments == {"letter_id": letter.id},
                Task.execute_at == expected_send_at,
            )
        ).one_or_none()
        assert rescheduled_send_task is not None

    def test_second_deferral_caller_does_not_send_waiting_response_email(
        self, db_session: Session
    ) -> None:
        """Idempotent deferral must not email non-responders a second time."""
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        send_at = datetime.now(tz=UTC) - timedelta(minutes=1)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=send_at,
        )
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=members[0])
        db_session.commit()

        with (
            run_scheduled_jobs_inline(db_session),
            patch(
                "ring.tasks.crud.task.send_email", return_value="message-id"
            ) as mock_send_email,
        ):
            assert (
                defer_letter_send_if_below_threshold(db_session, letter)
                is True
            )
            assert defer_letter_send(db_session, letter) is False

        mock_send_email.assert_called_once()
        assert is_waiting_response_email(mock_send_email)
        assert set(email_draft_recipients(mock_send_email)) == {
            member.email for member in members[1:]
        }

    def test_execute_send_email_task_sends_when_responders_meet_threshold(
        self, db_session: Session
    ) -> None:
        """Send letter immediately when enough participants have responded."""
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        send_at = datetime.now(tz=UTC) + timedelta(days=1)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=send_at,
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
            ) as mock_send_email,
        ):
            task_crud.execute_send_email_task(db_session, send_task)

        mock_send_email.assert_called_once()
        assert not is_waiting_response_email(mock_send_email)
        assert set(email_draft_recipients(mock_send_email)) == {
            member.email for member in members
        }
        db_session.refresh(letter)
        assert letter.status == LetterStatus.SENT
        assert letter.send_at == send_at

    def test_execute_send_email_task_respects_configured_min_responders(
        self, db_session: Session
    ) -> None:
        """Use per-group configured minimum responder count when provided."""
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        group.key_values.set_value(GROUP_SETTING_MIN_RESPONDERS_KEY, 3)
        send_at = datetime.now(tz=UTC) - timedelta(minutes=1)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=send_at,
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
        send_task.status = TaskStatus.IN_PROGRESS
        db_session.commit()

        with (
            run_scheduled_jobs_inline(db_session),
            patch(
                "ring.tasks.crud.task.send_email", return_value="message-id"
            ) as mock_send_email,
        ):
            task_crud.execute_send_email_task(db_session, send_task)

        mock_send_email.assert_called_once()
        assert is_waiting_response_email(mock_send_email)
        assert set(email_draft_recipients(mock_send_email)) == {
            members[2].email,
            members[3].email,
        }
        db_session.refresh(letter)
        assert letter.send_at == send_at + timedelta(
            days=LETTER_SEND_DEFERRAL_DAYS
        )

    def test_execute_send_email_task_ignores_invalid_threshold_config(
        self, db_session: Session
    ) -> None:
        """Fallback to default threshold when config value is invalid."""
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        group.key_values.set_value(
            GROUP_SETTING_MIN_RESPONDERS_KEY, "not-a-number"
        )
        send_at = datetime.now(tz=UTC) + timedelta(days=1)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=send_at,
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
            ) as mock_send_email,
        ):
            task_crud.execute_send_email_task(db_session, send_task)

        mock_send_email.assert_called_once()
        assert not is_waiting_response_email(mock_send_email)
        db_session.refresh(letter)
        assert letter.status == LetterStatus.SENT

    def test_execute_send_email_task_respects_configured_ratio(
        self, db_session: Session
    ) -> None:
        """Use per-group responder ratio config when min responders unset."""
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        group.key_values.set_value(GROUP_SETTING_MIN_RESPONDER_RATIO_KEY, 0.75)
        send_at = datetime.now(tz=UTC) - timedelta(minutes=1)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=send_at,
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
        send_task.status = TaskStatus.IN_PROGRESS
        db_session.commit()

        with (
            run_scheduled_jobs_inline(db_session),
            patch(
                "ring.tasks.crud.task.send_email", return_value="message-id"
            ) as mock_send_email,
        ):
            task_crud.execute_send_email_task(db_session, send_task)

        mock_send_email.assert_called_once()
        assert is_waiting_response_email(mock_send_email)
        db_session.refresh(letter)
        assert letter.send_at == send_at + timedelta(
            days=LETTER_SEND_DEFERRAL_DAYS
        )

    def test_execute_send_email_task_sends_when_threshold_disabled(
        self, db_session: Session
    ) -> None:
        """Send on schedule when responder ratio is explicitly set to zero."""
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        group.key_values.set_value(GROUP_SETTING_MIN_RESPONDER_RATIO_KEY, 0)
        send_at = datetime.now(tz=UTC) + timedelta(days=1)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=send_at,
        )
        QuestionFactory.create(letter=letter)
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
            ) as mock_send_email,
        ):
            task_crud.execute_send_email_task(db_session, send_task)

        mock_send_email.assert_called_once()
        assert not is_waiting_response_email(mock_send_email)
        db_session.refresh(letter)
        assert letter.status == LetterStatus.SENT

    def test_send_waiting_response_email_noops_without_non_responders(
        self, db_session: Session
    ) -> None:
        """Skip sending when every participant has already answered."""
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=datetime.now(tz=UTC) - timedelta(minutes=1),
        )
        question = QuestionFactory.create(letter=letter)
        for member in members:
            ResponseFactory.create(question=question, participant=member)
        db_session.commit()

        with patch(
            "ring.tasks.crud.task.send_email", return_value="message-id"
        ) as mock_send_email:
            from ring.async_scheduler.job_registry import JOB_REGISTRY

            JOB_REGISTRY["send_waiting_response_email"].job_function(
                db_session, letter.id
            )

        mock_send_email.assert_not_called()

    def test_execute_send_email_task_skips_after_postpend_deferral(
        self, db_session: Session
    ) -> None:
        """A send job queued for the old deadline must not send after deferral."""
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        send_at = datetime.now(tz=UTC) - timedelta(minutes=1)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=send_at,
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
        send_task.status = TaskStatus.IN_PROGRESS
        db_session.commit()

        with (
            run_scheduled_jobs_inline(db_session),
            patch(
                "ring.tasks.crud.task.send_email", return_value="message-id"
            ) as mock_send_email,
        ):
            letter_crud.postpend_upcoming_letters_with_session(
                db_session, [letter.id]
            )
            task_crud.execute_send_email_task(db_session, send_task)

        mock_send_email.assert_called_once()
        assert is_waiting_response_email(mock_send_email)
        db_session.refresh(letter)
        assert letter.status == LetterStatus.IN_PROGRESS
        assert letter.send_at == send_at + timedelta(
            days=LETTER_SEND_DEFERRAL_DAYS
        )

    def test_execute_send_email_task_skips_stale_task_even_if_threshold_met(
        self, db_session: Session
    ) -> None:
        """Deferral invalidates this job even if answers arrive before it runs."""
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        send_at = datetime.now(tz=UTC) - timedelta(minutes=1)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=send_at,
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
        send_task.status = TaskStatus.IN_PROGRESS
        db_session.commit()

        with (
            run_scheduled_jobs_inline(db_session),
            patch(
                "ring.tasks.crud.task.send_email", return_value="message-id"
            ) as mock_send_email,
        ):
            letter_crud.postpend_upcoming_letters_with_session(
                db_session, [letter.id]
            )
            ResponseFactory.create(question=question, participant=members[1])
            db_session.commit()
            task_crud.execute_send_email_task(db_session, send_task)

        mock_send_email.assert_called_once()
        assert is_waiting_response_email(mock_send_email)
        db_session.refresh(letter)
        assert letter.status == LetterStatus.IN_PROGRESS
        assert letter.send_at == send_at + timedelta(
            days=LETTER_SEND_DEFERRAL_DAYS
        )
