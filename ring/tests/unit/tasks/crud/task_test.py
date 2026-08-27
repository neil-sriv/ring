"""Tests for task CRUD execution behavior."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from ring.letters.constants import LetterStatus
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

    def test_requeue_in_progress_tasks_resets_stranded_tasks(
        self, db_session: Session
    ) -> None:
        """Put stranded IN_PROGRESS tasks back in PENDING at startup.

        Regression test: a restart or deploy wipes the APScheduler
        jobstore, so tasks claimed by the previous process stayed
        IN_PROGRESS forever — never re-collected by the poll loop, while
        the postpend job skipped their letters because a send task still
        appeared responsible. The letter behind the task was frozen: no
        email, no deferral, nothing at its due date.
        """
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin])
        db_session.commit()
        stranded = schedule_crud.register_task(
            db_session,
            group.schedule,
            TaskType.SEND_EMAIL,
            datetime.now(tz=UTC) - timedelta(hours=1),
            {"letter_id": None},
        )
        stranded.status = TaskStatus.IN_PROGRESS
        completed = schedule_crud.register_task(
            db_session,
            group.schedule,
            TaskType.REMINDER_EMAIL,
            datetime.now(tz=UTC) - timedelta(days=1),
            {"letter_id": None},
        )
        completed.status = TaskStatus.COMPLETED
        db_session.commit()

        requeued = task_crud.requeue_in_progress_tasks(db_session)

        assert requeued == 1
        db_session.expire_all()
        assert stranded.status == TaskStatus.PENDING
        assert "requeued at startup" in stranded.message
        assert completed.status == TaskStatus.COMPLETED

    def test_requeue_orphaned_in_progress_tasks_skips_when_jobs_remain(
        self, db_session: Session
    ) -> None:
        """Do not requeue a send that still has a one-shot scheduler job."""
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin])
        db_session.commit()
        stranded = schedule_crud.register_task(
            db_session,
            group.schedule,
            TaskType.SEND_EMAIL,
            datetime.now(tz=UTC) - timedelta(hours=1),
            {"letter_id": None},
        )
        stranded.status = TaskStatus.IN_PROGRESS
        db_session.commit()

        running_job = type("Job", (), {"id": "send_email_task_running"})()
        with patch(
            "ring.tasks.crud.task.scheduler.get_jobs",
            return_value=[running_job],
        ):
            requeued = task_crud.requeue_orphaned_in_progress_tasks(db_session)

        assert requeued == 0
        db_session.expire_all()
        assert stranded.status == TaskStatus.IN_PROGRESS

    def test_requeue_orphaned_in_progress_tasks_resets_when_jobstore_empty(
        self, db_session: Session
    ) -> None:
        """Requeue IN_PROGRESS tasks when only interval jobs remain."""
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin])
        db_session.commit()
        stranded = schedule_crud.register_task(
            db_session,
            group.schedule,
            TaskType.SEND_EMAIL,
            datetime.now(tz=UTC) - timedelta(hours=1),
            {"letter_id": None},
        )
        stranded.status = TaskStatus.IN_PROGRESS
        db_session.commit()

        interval_job = type("Job", (), {"id": "poll_schedule_task"})()
        with (
            patch(
                "ring.tasks.crud.task.scheduler.get_jobs",
                return_value=[interval_job],
            ),
            patch(
                "ring.tasks.crud.task.INTERVAL_JOB_SCHEDULE_REGISTRY",
                {"poll_schedule_task": object()},
            ),
        ):
            requeued = task_crud.requeue_orphaned_in_progress_tasks(db_session)

        assert requeued == 1
        db_session.expire_all()
        assert stranded.status == TaskStatus.PENDING
        assert "no one-shot scheduler jobs" in stranded.message

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
