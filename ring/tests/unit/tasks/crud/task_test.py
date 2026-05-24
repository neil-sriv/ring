"""Tests for task CRUD execution behavior."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from sqlalchemy import select
from sqlalchemy.orm import Session

from ring.letters.constants import LetterStatus
from ring.tasks.crud import task as task_crud
from ring.tasks.models.task_model import Task, TaskStatus, TaskType
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.letters.response_factory import ResponseFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory


class TestTaskCrud:
    """Test suite for task execution logic."""

    def test_execute_send_email_task_defers_when_responders_below_threshold(
        self, db_session: Session
    ) -> None:
        """Defer send by one day when too few participants have responded."""
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

        with patch(
            "ring.tasks.crud.task.send_email", return_value="message-id"
        ) as mock_send_email:
            task_crud.execute_send_email_task(db_session, send_task)

        mock_send_email.assert_not_called()
        db_session.refresh(letter)

        expected_send_at = send_at + timedelta(
            days=task_crud.LETTER_SEND_DEFERRAL_DAYS
        )
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

        with patch(
            "ring.tasks.crud.task.send_email", return_value="message-id"
        ) as mock_send_email:
            task_crud.execute_send_email_task(db_session, send_task)

        mock_send_email.assert_called_once()
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
        group.key_values.set_value(
            task_crud.GROUP_SETTING_MIN_RESPONDERS_KEY, 3
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
        send_task.status = TaskStatus.IN_PROGRESS
        db_session.commit()

        with patch(
            "ring.tasks.crud.task.send_email", return_value="message-id"
        ) as mock_send_email:
            task_crud.execute_send_email_task(db_session, send_task)

        mock_send_email.assert_not_called()
        db_session.refresh(letter)
        assert letter.send_at == send_at + timedelta(
            days=task_crud.LETTER_SEND_DEFERRAL_DAYS
        )

    def test_execute_send_email_task_ignores_invalid_threshold_config(
        self, db_session: Session
    ) -> None:
        """Fallback to default threshold when config value is invalid."""
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        group.key_values.set_value(
            task_crud.GROUP_SETTING_MIN_RESPONDERS_KEY, "not-a-number"
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

        with patch(
            "ring.tasks.crud.task.send_email", return_value="message-id"
        ) as mock_send_email:
            task_crud.execute_send_email_task(db_session, send_task)

        mock_send_email.assert_called_once()
        db_session.refresh(letter)
        assert letter.status == LetterStatus.SENT

    def test_execute_send_email_task_respects_configured_ratio(
        self, db_session: Session
    ) -> None:
        """Use per-group responder ratio config when min responders unset."""
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        group.key_values.set_value(
            task_crud.GROUP_SETTING_MIN_RESPONDER_RATIO_KEY, 0.75
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
        send_task.status = TaskStatus.IN_PROGRESS
        db_session.commit()

        with patch(
            "ring.tasks.crud.task.send_email", return_value="message-id"
        ) as mock_send_email:
            task_crud.execute_send_email_task(db_session, send_task)

        mock_send_email.assert_not_called()
        db_session.refresh(letter)
        assert letter.send_at == send_at + timedelta(
            days=task_crud.LETTER_SEND_DEFERRAL_DAYS
        )
