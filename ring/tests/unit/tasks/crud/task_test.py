"""Tests for task CRUD execution behavior."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from ring.fastapp.config import get_config
from ring.fastapp.fast import app
from ring.letters.constants import LetterStatus
from ring.letters.crud import letter as letter_crud
from ring.letters.send_threshold import (
    GROUP_SETTING_MIN_RESPONDER_RATIO_KEY,
    GROUP_SETTING_MIN_RESPONDERS_KEY,
    LETTER_SEND_DEFERRAL_DAYS,
    defer_letter_send,
    defer_letter_send_if_below_threshold,
)
from ring.tasks.crud import schedule as schedule_crud
from ring.tasks.crud import task as task_crud
from ring.tasks.models.task_model import (
    ReminderEmailTask,
    SendEmailTask,
    Task,
    TaskStatus,
    TaskType,
)
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


def _assert_deferred_into_future(actual: datetime) -> None:
    """A deferral anchored on now lands one day ahead, not on the old date."""
    skew = actual - (
        datetime.now(tz=UTC) + timedelta(days=LETTER_SEND_DEFERRAL_DAYS)
    )
    assert abs(skew.total_seconds()) < 30
    assert actual > datetime.now(tz=UTC)


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

        _assert_deferred_into_future(letter.send_at)
        expected_send_at = letter.send_at
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
                "ring.letters.crud.letter.send_email",
                return_value="message-id",
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
        _assert_deferred_into_future(letter.send_at)

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
                "ring.letters.crud.letter.send_email",
                return_value="message-id",
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
        _assert_deferred_into_future(letter.send_at)

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
                "ring.letters.crud.letter.send_email",
                return_value="message-id",
            ) as mock_send_email,
        ):
            task_crud.execute_send_email_task(db_session, send_task)

        mock_send_email.assert_called_once()
        assert not is_waiting_response_email(mock_send_email)
        db_session.refresh(letter)
        assert letter.status == LetterStatus.SENT

    def test_execute_send_email_task_creates_next_letter_when_missing(
        self, db_session: Session
    ) -> None:
        """Keep the cadence going for groups without an upcoming letter."""
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
        for member in members:
            ResponseFactory.create(question=question, participant=member)
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
                "ring.letters.crud.letter.send_email",
                return_value="message-id",
            ) as mock_send_email,
        ):
            task_crud.execute_send_email_task(
                db_session, send_task, letter_id=letter.id
            )

        mock_send_email.assert_called_once()
        db_session.refresh(letter)
        assert letter.status == LetterStatus.SENT
        assert len(group.upcoming_letters) == 1
        assert group.upcoming_letters[0].send_at == send_at + timedelta(
            days=group.cycle_length
        )

    def test_execute_send_email_task_skips_already_sent_letter(
        self, db_session: Session
    ) -> None:
        """Never email a letter twice when its status is already SENT."""
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=datetime.now(tz=UTC) - timedelta(minutes=1),
        )
        db_session.commit()

        send_task = db_session.scalars(
            select(Task).where(
                Task.schedule_id == group.schedule.id,
                Task.type == TaskType.SEND_EMAIL,
                Task.arguments == {"letter_id": letter.id},
            )
        ).one()
        letter.status = LetterStatus.SENT
        db_session.commit()

        with (
            run_scheduled_jobs_inline(db_session),
            patch(
                "ring.letters.crud.letter.send_email",
                return_value="message-id",
            ) as mock_send_email,
        ):
            task_crud.execute_send_email_task(
                db_session, send_task, letter_id=letter.id
            )

        mock_send_email.assert_not_called()
        db_session.refresh(letter)
        assert letter.status == LetterStatus.SENT

    def test_execute_send_email_task_handles_legacy_task_without_letter(
        self, db_session: Session
    ) -> None:
        """Complete gracefully when a legacy task has no letter to send.

        Tasks registered before letter ids were stored carry
        ``{"letter_id": None}`` and fall back to the group's in-progress
        letter; when there is none the task must not crash.
        """
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin])
        db_session.commit()
        send_task = schedule_crud.register_task(
            db_session,
            group.schedule,
            TaskType.SEND_EMAIL,
            datetime.now(tz=UTC) - timedelta(minutes=1),
            {"letter_id": None},
        )
        db_session.commit()

        with (
            run_scheduled_jobs_inline(db_session),
            patch(
                "ring.letters.crud.letter.send_email",
                return_value="message-id",
            ) as mock_send_email,
        ):
            task_crud.execute_send_email_task(
                db_session, send_task, letter_id=None
            )

        mock_send_email.assert_not_called()

    def test_find_and_execute_task_requeues_on_transient_database_error(
        self, db_session: Session
    ) -> None:
        """Put tasks back in PENDING when the database aborts the write.

        Regression test: CockroachDB serialization failures marked the task
        FAILED forever, so the letter email was never retried and the letter
        was silently never sent.
        """
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin])
        db_session.commit()
        send_task = schedule_crud.register_task(
            db_session,
            group.schedule,
            TaskType.SEND_EMAIL,
            datetime.now(tz=UTC) - timedelta(minutes=1),
            {"letter_id": None},
        )
        db_session.commit()
        task_id = send_task.id

        def raise_transient_error(*args: object, **kwargs: object) -> None:
            raise OperationalError(
                "UPDATE letter", {}, Exception("restart transaction")
            )

        # The test session joins the fixture's outer transaction, so a real
        # rollback would wipe the task INSERT itself (in production the row
        # is already committed). Stub it out: the behavior under test is
        # the PENDING status transition, not rollback mechanics.
        with (
            patch.object(db_session, "rollback"),
            pytest.raises(OperationalError),
        ):
            task_crud._find_and_execute_task(
                db_session,
                task_id,
                SendEmailTask,
                raise_transient_error,
            )

        db_session.expire_all()
        requeued = db_session.scalars(
            select(Task).where(Task.id == task_id)
        ).one()
        assert requeued.status == TaskStatus.PENDING
        assert "transient database error" in requeued.message

    def test_transient_error_after_email_does_not_requeue(
        self, db_session: Session
    ) -> None:
        """Do not retry a send or reminder once its email has gone out.

        Regression: two stale send tasks deferred the same letter, the
        waiting-response email was accepted, then CockroachDB raised
        WriteTooOldError. The task was put back in PENDING and the next
        poll sent the email again.
        """
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin])
        db_session.commit()

        def send_then_fail(*args: object, **kwargs: object) -> None:
            task_crud._note_email_dispatched()
            raise OperationalError(
                "UPDATE letter", {}, Exception("WriteTooOldError")
            )

        cases = (
            (TaskType.SEND_EMAIL, SendEmailTask),
            (TaskType.REMINDER_EMAIL, ReminderEmailTask),
        )
        for task_type, task_class in cases:
            task = schedule_crud.register_task(
                db_session,
                group.schedule,
                task_type,
                datetime.now(tz=UTC) - timedelta(minutes=1),
                {"letter_id": None},
            )
            db_session.commit()
            task_id = task.id
            with (
                patch.object(db_session, "rollback"),
                pytest.raises(OperationalError),
            ):
                task_crud._find_and_execute_task(
                    db_session,
                    task_id,
                    task_class,
                    send_then_fail,
                )

            db_session.expire_all()
            failed = db_session.scalars(
                select(Task).where(Task.id == task_id)
            ).one()
            assert failed.status == TaskStatus.FAILED
            assert "email already sent" in failed.message
            assert "not retrying" in failed.message

    def test_deferral_persist_failure_does_not_send_email(
        self, db_session: Session
    ) -> None:
        """A deferral that fails to commit must not email non-responders."""
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=datetime.now(tz=UTC) - timedelta(minutes=1),
        )
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=members[0])
        db_session.commit()

        def fail_commit() -> None:
            raise OperationalError("COMMIT", {}, Exception("WriteTooOldError"))

        with (
            patch("ring.tasks.crud.task.send_email") as mock_send_email,
            patch.object(db_session, "commit", fail_commit),
            pytest.raises(OperationalError),
        ):
            defer_letter_send_if_below_threshold(db_session, letter)

        mock_send_email.assert_not_called()

    def test_stale_send_and_reminder_tasks_are_not_executed(
        self, db_session: Session
    ) -> None:
        """Reminder tasks older than 48h are failed and not run.

        Send tasks still run so the letter can be deferred without an
        email. A 47h-old send task is unchanged.
        """
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin])
        db_session.commit()
        now = datetime.now(tz=UTC)
        stale_send = schedule_crud.register_task(
            db_session,
            group.schedule,
            TaskType.SEND_EMAIL,
            now - timedelta(hours=49),
            {"letter_id": None},
        )
        stale_reminder = schedule_crud.register_task(
            db_session,
            group.schedule,
            TaskType.REMINDER_EMAIL,
            now - timedelta(hours=49),
            {"letter_id": None},
        )
        recent_send = schedule_crud.register_task(
            db_session,
            group.schedule,
            TaskType.SEND_EMAIL,
            now - timedelta(hours=47),
            {"letter_id": None},
        )
        db_session.commit()

        scheduled: list[int] = []
        with patch(
            "ring.tasks.crud.task.scheduler.add_job",
            side_effect=lambda job, args, kwargs: scheduled.append(args[0]),
        ):
            task_crud.execute_tasks(
                db_session,
                [stale_send.id, stale_reminder.id, recent_send.id],
            )

        assert set(scheduled) == {stale_send.id, recent_send.id}
        assert stale_reminder.status == TaskStatus.FAILED
        assert "48h" in stale_reminder.message
        assert stale_send.status == TaskStatus.IN_PROGRESS
        assert recent_send.status == TaskStatus.IN_PROGRESS

        executed = False

        def execute(*args: object, **kwargs: object) -> None:
            nonlocal executed
            executed = True

        task_crud._find_and_execute_task(
            db_session,
            stale_reminder.id,
            ReminderEmailTask,
            execute,
        )
        assert executed is False
        assert stale_reminder.status == TaskStatus.FAILED

    def test_app_startup_leaves_in_progress_tasks_unchanged(
        self, db_session: Session
    ) -> None:
        """App startup must not reset IN_PROGRESS tasks to PENDING.

        Regression: the lifespan called requeue_in_progress_tasks with
        no age bound, so every restart flipped stale send and reminder
        rows back to PENDING and the poll loop emailed them.
        """
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin])
        db_session.commit()
        claimed = schedule_crud.register_task(
            db_session,
            group.schedule,
            TaskType.SEND_EMAIL,
            datetime.now(tz=UTC) - timedelta(days=90),
            {"letter_id": None},
        )
        claimed.status = TaskStatus.IN_PROGRESS
        claimed.message = "claimed by the previous process"
        completed = schedule_crud.register_task(
            db_session,
            group.schedule,
            TaskType.REMINDER_EMAIL,
            datetime.now(tz=UTC) - timedelta(days=1),
            {"letter_id": None},
        )
        completed.status = TaskStatus.COMPLETED
        completed.message = "sent"
        db_session.commit()

        enabled = get_config().model_copy(update={"DISABLE_SCHEDULER": False})

        @contextmanager
        def _startup_session() -> Iterator[Session]:
            yield db_session

        with (
            patch("ring.fastapp.fast.get_config", return_value=enabled),
            patch("ring.fastapp.fast.scheduler.start") as start,
            patch("ring.fastapp.fast.scheduler.shutdown"),
            patch(
                "ring.fastapp.fast.SessionLocal",
                _startup_session,
                create=True,
            ),
            patch(
                "ring.sqlalchemy_base.SessionLocal",
                _startup_session,
            ),
        ):
            with TestClient(app):
                pass

        start.assert_called_once()
        db_session.expire_all()
        assert claimed.status == TaskStatus.IN_PROGRESS
        assert claimed.message == "claimed by the previous process"
        assert completed.status == TaskStatus.COMPLETED
        assert completed.message == "sent"

    def test_execute_tasks_skips_task_without_executor(
        self, db_session: Session
    ) -> None:
        """One task without an executor must not block the whole batch."""
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin])
        db_session.commit()
        generic_task = schedule_crud.register_task(
            db_session,
            group.schedule,
            TaskType.GENERIC,
            datetime.now(tz=UTC) - timedelta(minutes=1),
        )
        send_task = schedule_crud.register_task(
            db_session,
            group.schedule,
            TaskType.SEND_EMAIL,
            datetime.now(tz=UTC) - timedelta(minutes=1),
            {"letter_id": None},
        )
        db_session.commit()

        scheduled_jobs: list[int] = []
        with patch(
            "ring.tasks.crud.task.scheduler.add_job",
            side_effect=lambda job, args, kwargs: scheduled_jobs.append(
                args[0]
            ),
        ):
            task_crud.execute_tasks(
                db_session, [generic_task.id, send_task.id]
            )

        assert scheduled_jobs == [send_task.id]
        assert generic_task.status == TaskStatus.FAILED
        assert "no executor registered" in generic_task.message
        assert send_task.status == TaskStatus.IN_PROGRESS

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
        """A send job queued for the old deadline must not send after deferral.

        Postpend skips a letter that still has a pending or in-progress
        send task, so this task is failed first and postpend can move
        send_at while the old execute_at stays put.
        """
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
        send_task.status = TaskStatus.FAILED
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
        _assert_deferred_into_future(letter.send_at)

    def test_execute_send_email_task_skips_stale_task_even_if_threshold_met(
        self, db_session: Session
    ) -> None:
        """Deferral invalidates this job even if answers arrive before it runs.

        The send task is failed first so postpend can push send_at. The
        failed task keeps its original execute_at, so running it afterward
        is the stale invocation.
        """
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
        send_task.status = TaskStatus.FAILED
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
        _assert_deferred_into_future(letter.send_at)
