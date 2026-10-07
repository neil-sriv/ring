"""Tests for postpend letter behavior with send thresholds."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from sqlalchemy import select
from sqlalchemy.orm import Session

from ring.letters.constants import LetterStatus
from ring.letters.crud import letter as letter_crud
from ring.letters.models.letter_model import Letter
from ring.letters.send_threshold import (
    LETTER_SEND_DEFERRAL_DAYS,
    defer_letter_send_if_below_threshold,
    hold_letter_for_send_threshold,
)
from ring.tasks.crud import schedule as schedule_crud
from ring.tasks.crud import task as task_crud
from ring.tasks.models.task_model import Task, TaskStatus, TaskType
from ring.tests.factories.letters.letter_factory import (
    LetterFactory,
    UpcomingLetterFactory,
)
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.letters.response_factory import ResponseFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory
from ring.tests.lib.utils import (
    email_draft_recipients,
    is_waiting_response_email,
    run_scheduled_jobs_inline,
)


def _run_schedule_poll(db_session: Session) -> None:
    """Run one poll's task execution and postpend, in that order."""
    now = datetime.now(tz=UTC)
    tasks = schedule_crud.collect_pending_tasks(db_session, now)
    if tasks:
        task_crud.execute_tasks(db_session, [task.id for task in tasks])
    postpend, _promote = letter_crud.collect_future_letters(db_session, now)
    if postpend:
        letter_crud.postpend_upcoming_letters_with_session(
            db_session, [letter.id for letter in postpend]
        )


def _assert_deferred_into_future(actual: datetime) -> None:
    """A deferral anchored on now lands one day ahead, not on the old date."""
    skew = actual - (
        datetime.now(tz=UTC) + timedelta(days=LETTER_SEND_DEFERRAL_DAYS)
    )
    assert abs(skew.total_seconds()) < 30
    assert actual > datetime.now(tz=UTC)


class TestPostpendLetters:
    """Tests for postpend_upcoming_letters threshold handling."""

    def run_postpend_job(
        self, db_session: Session, letter_ids: list[int]
    ) -> None:
        letter_crud.postpend_upcoming_letters_with_session(
            db_session, letter_ids
        )

    def orphan_send_task(self, db_session: Session, letter: Letter) -> None:
        """Fail the letter's send-email task so postpend owns the letter."""
        send_task = db_session.scalars(
            select(Task).where(
                Task.schedule_id == letter.group.schedule.id,
                Task.type == TaskType.SEND_EMAIL,
                Task.execute_at == letter.send_at,
            )
        ).one()
        send_task.status = TaskStatus.FAILED
        db_session.commit()

    def test_postpend_defers_when_responders_below_threshold(
        self, db_session: Session
    ) -> None:
        """Do not mark SENT when threshold is unmet; defer send instead."""
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
        self.orphan_send_task(db_session, letter)

        with (
            run_scheduled_jobs_inline(db_session),
            patch(
                "ring.tasks.crud.task.send_email", return_value="message-id"
            ) as mock_send_email,
        ):
            self.run_postpend_job(db_session, [letter.id])

        mock_send_email.assert_called_once()
        assert is_waiting_response_email(mock_send_email)
        assert set(email_draft_recipients(mock_send_email)) == {
            member.email for member in members[1:]
        }
        assert members[0].email not in email_draft_recipients(mock_send_email)

        db_session.refresh(letter)

        assert letter.status == LetterStatus.IN_PROGRESS
        _assert_deferred_into_future(letter.send_at)

    def test_postpend_does_not_defer_before_send_date(
        self, db_session: Session
    ) -> None:
        """Leave the send date alone when the deadline has not arrived yet."""
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        send_at = datetime.now(tz=UTC) + timedelta(days=5)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=send_at,
        )
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=members[0])
        db_session.commit()

        with (
            run_scheduled_jobs_inline(db_session) as mock_add_job,
            patch(
                "ring.tasks.crud.task.send_email", return_value="message-id"
            ) as mock_send_email,
        ):
            self.run_postpend_job(db_session, [letter.id])

        mock_add_job.assert_not_called()
        mock_send_email.assert_not_called()
        db_session.refresh(letter)

        assert letter.status == LetterStatus.IN_PROGRESS
        assert letter.send_at == send_at

    def test_repeated_postpend_polls_defer_send_date_once(
        self, db_session: Session
    ) -> None:
        """Deferring once moves the deadline out of reach of later polls."""
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
        self.orphan_send_task(db_session, letter)

        with (
            run_scheduled_jobs_inline(db_session),
            patch(
                "ring.tasks.crud.task.send_email", return_value="message-id"
            ) as mock_send_email,
        ):
            for _ in range(3):
                self.run_postpend_job(db_session, [letter.id])

        mock_send_email.assert_called_once()
        assert is_waiting_response_email(mock_send_email)
        db_session.refresh(letter)

        assert letter.status == LetterStatus.IN_PROGRESS
        _assert_deferred_into_future(letter.send_at)

    def test_polls_email_once_when_deferred_date_would_stay_past(
        self, db_session: Session
    ) -> None:
        """One waiting email across polls when send_at + 1 day is still past.

        Regression: deferral added a day to the old send_at, so the letter
        stayed overdue. Every poll listed it for postpend, created another
        send task, and sent another waiting-response email.
        """
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=datetime.now(tz=UTC) - timedelta(hours=36),
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
            for _ in range(3):
                _run_schedule_poll(db_session)

        waiting_calls = [
            index
            for index in range(mock_send_email.call_count)
            if is_waiting_response_email(mock_send_email, index)
        ]
        assert len(waiting_calls) == 1
        db_session.refresh(letter)
        assert letter.status == LetterStatus.IN_PROGRESS
        _assert_deferred_into_future(letter.send_at)

    def test_polls_skip_email_when_send_at_is_more_than_48h_past(
        self, db_session: Session
    ) -> None:
        """A long-overdue letter is deferred forward and not emailed.

        The group is over the send threshold, so the only thing stopping
        the letter email is the 48h cutoff.
        """
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=datetime.now(tz=UTC) - timedelta(days=10),
        )
        question = QuestionFactory.create(letter=letter)
        for member in members:
            ResponseFactory.create(question=question, participant=member)
        db_session.commit()

        with (
            run_scheduled_jobs_inline(db_session),
            patch(
                "ring.tasks.crud.task.send_email", return_value="message-id"
            ) as task_send_email,
            patch(
                "ring.letters.crud.letter.send_email",
                return_value="message-id",
            ) as letter_send_email,
        ):
            for _ in range(3):
                _run_schedule_poll(db_session)

        task_send_email.assert_not_called()
        letter_send_email.assert_not_called()
        db_session.refresh(letter)
        assert letter.status == LetterStatus.IN_PROGRESS
        _assert_deferred_into_future(letter.send_at)

    def test_send_email_and_postpend_defer_send_date_once(
        self, db_session: Session
    ) -> None:
        """At deadline, send-email and postpend must not stack two deferrals."""
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
            assert hold_letter_for_send_threshold(db_session, letter) is True

        mock_send_email.assert_called_once()
        assert is_waiting_response_email(mock_send_email)
        assert set(email_draft_recipients(mock_send_email)) == {
            member.email for member in members[1:]
        }
        db_session.refresh(letter)

        assert letter.status == LetterStatus.IN_PROGRESS
        _assert_deferred_into_future(letter.send_at)

    def test_postpend_then_send_email_defers_send_date_once(
        self, db_session: Session
    ) -> None:
        """Postpend-first (the live job order) must not send or stack days."""
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
            assert hold_letter_for_send_threshold(db_session, letter) is True
            assert (
                defer_letter_send_if_below_threshold(db_session, letter)
                is True
            )

        mock_send_email.assert_called_once()
        assert is_waiting_response_email(mock_send_email)
        db_session.refresh(letter)

        assert letter.status == LetterStatus.IN_PROGRESS
        _assert_deferred_into_future(letter.send_at)

    def test_postpend_sends_and_marks_sent_when_threshold_met(
        self, db_session: Session
    ) -> None:
        """Email an orphaned due letter, mark it SENT, and create the next one.

        Regression test: postpend used to mark overdue letters SENT without
        ever emailing them, silently swallowing the letter whenever its
        send-email task had failed.
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
        ResponseFactory.create(question=question, participant=members[1])
        db_session.commit()
        self.orphan_send_task(db_session, letter)

        with (
            run_scheduled_jobs_inline(db_session) as mock_add_job,
            patch(
                "ring.letters.crud.letter.send_email",
                return_value="message-id",
            ) as mock_letter_email,
        ):
            self.run_postpend_job(db_session, [letter.id])

        mock_add_job.assert_not_called()
        mock_letter_email.assert_called_once()
        assert set(email_draft_recipients(mock_letter_email)) == {
            member.email for member in members
        }
        db_session.refresh(letter)

        assert letter.status == LetterStatus.SENT
        assert len(letter.group.upcoming_letters) == 1

    def test_postpend_skips_letter_with_outstanding_send_task(
        self, db_session: Session
    ) -> None:
        """Leave letters alone while a send-email task still owns them.

        Regression test: at the send deadline the poll job schedules the
        letter's send-email task and the postpend job in the same cycle;
        postpend used to mark the letter SENT concurrently, racing the send
        task and closing the letter without an email.
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
        for member in members:
            ResponseFactory.create(question=question, participant=member)
        db_session.commit()

        with (
            run_scheduled_jobs_inline(db_session) as mock_add_job,
            patch(
                "ring.letters.crud.letter.send_email",
                return_value="message-id",
            ) as mock_letter_email,
        ):
            self.run_postpend_job(db_session, [letter.id])

        mock_add_job.assert_not_called()
        mock_letter_email.assert_not_called()
        db_session.refresh(letter)

        assert letter.status == LetterStatus.IN_PROGRESS
        assert letter.send_at == send_at

    def test_postpend_keeps_letter_open_when_email_fails(
        self, db_session: Session
    ) -> None:
        """Do not mark SENT when the letter email is not accepted."""
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
        self.orphan_send_task(db_session, letter)

        with (
            run_scheduled_jobs_inline(db_session),
            patch(
                "ring.letters.crud.letter.send_email", return_value=None
            ) as mock_letter_email,
        ):
            self.run_postpend_job(db_session, [letter.id])

        mock_letter_email.assert_called_once()
        db_session.refresh(letter)

        assert letter.status == LetterStatus.IN_PROGRESS
        assert letter.group.upcoming_letters == []

    def test_postpend_does_not_duplicate_upcoming_letter(
        self, db_session: Session
    ) -> None:
        """Recover a lost send without creating a second upcoming letter."""
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        send_at = datetime.now(tz=UTC) - timedelta(minutes=1)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=send_at,
        )
        upcoming = UpcomingLetterFactory.create(
            group=group,
            send_at=send_at + timedelta(days=group.cycle_length),
        )
        question = QuestionFactory.create(letter=letter)
        for member in members:
            ResponseFactory.create(question=question, participant=member)
        db_session.commit()
        self.orphan_send_task(db_session, letter)

        with (
            run_scheduled_jobs_inline(db_session),
            patch(
                "ring.letters.crud.letter.send_email",
                return_value="message-id",
            ) as mock_letter_email,
        ):
            self.run_postpend_job(db_session, [letter.id])

        mock_letter_email.assert_called_once()
        db_session.refresh(letter)

        assert letter.status == LetterStatus.SENT
        assert letter.group.upcoming_letters == [upcoming]

    def test_postpend_keeps_future_letter_open_when_threshold_met(
        self, db_session: Session
    ) -> None:
        """Never mark SENT before the send date, even at full participation.

        Regression test: the poll job used to collect in-progress letters up
        to a week before their send date, and postpend marked them SENT as
        soon as the responder threshold was met — closing the response window
        days early.
        """
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        send_at = datetime.now(tz=UTC) + timedelta(days=6)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=send_at,
        )
        question = QuestionFactory.create(letter=letter)
        for member in members:
            ResponseFactory.create(question=question, participant=member)
        db_session.commit()

        with (
            run_scheduled_jobs_inline(db_session) as mock_add_job,
            patch(
                "ring.tasks.crud.task.send_email", return_value="message-id"
            ) as mock_send_email,
        ):
            self.run_postpend_job(db_session, [letter.id])

        mock_add_job.assert_not_called()
        mock_send_email.assert_not_called()
        db_session.refresh(letter)

        assert letter.status == LetterStatus.IN_PROGRESS
        assert letter.send_at == send_at
