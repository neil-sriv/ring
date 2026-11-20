"""Tests for the batched late-question email."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from ring.async_scheduler.job_registry import JOB_REGISTRY
from ring.letters.constants import (
    LATE_QUESTION_EMAIL_DELAY,
    LATE_QUESTION_EMAIL_MAX_ATTEMPTS,
    LATE_QUESTION_EMAIL_RETRY_BACKOFF,
    LATE_QUESTION_EMAIL_WINDOW,
    LetterStatus,
)
from ring.letters.crud.question import delete_question
from ring.letters.models.letter_model import Letter
from ring.lib.app_links import app_url
from ring.tasks.crud import task as task_crud  # noqa: F401
from ring.tasks.crud.late_question_email_task import (
    construct_late_question_email,
)
from ring.tasks.models.task_model import Task, TaskStatus, TaskType
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.letters.response_factory import ResponseFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory


def _add_question(
    client: TestClient,
    letter: Letter,
    question_text: str,
    author_api_id: str | None,
):
    return client.post(
        f"/letters/letter/{letter.api_identifier}:add_question",
        json={
            "question_text": question_text,
            "author_api_id": author_api_id,
        },
    )


def _late_question_tasks(db: Session, letter: Letter) -> list[Task]:
    return list(
        db.scalars(
            select(Task)
            .where(
                Task.schedule_id == letter.group.schedule.id,
                Task.type == TaskType.LATE_QUESTION_EMAIL,
            )
            .order_by(Task.id)
        ).all()
    )


def _run_pending(db: Session, letter: Letter) -> Task:
    pending = [
        task
        for task in _late_question_tasks(db, letter)
        if task.status == TaskStatus.PENDING
    ]
    assert len(pending) == 1
    task = pending[0]
    JOB_REGISTRY["send_late_question_email"].job_function(
        db,
        task.id,
        **task.arguments,
    )
    db.refresh(task)
    db.refresh(letter)
    return task


class TestLateQuestionEmail:
    def test_one_email_lists_both_questions_for_responders_only(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: UserFactory,
    ) -> None:
        """Two late questions in one day produce one email.

        Recipients are participants who already replied, minus the author.
        A participant with no responses is left out.
        """
        responder = UserFactory.create()
        silent = UserFactory.create()
        group = GroupFactory.create(
            admin=current_user,
            members=[current_user, responder, silent],
        )
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            title="Spring",
            send_at=datetime.now(tz=UTC) + timedelta(days=3),
        )
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=current_user)
        ResponseFactory.create(question=question, participant=responder)
        db_session.commit()

        first = _add_question(
            authenticated_client,
            letter,
            "First late question?",
            current_user.api_identifier,
        )
        second = _add_question(
            authenticated_client,
            letter,
            "Second late question?",
            current_user.api_identifier,
        )
        assert first.status_code == 200
        assert second.status_code == 200

        pending = [
            task
            for task in _late_question_tasks(db_session, letter)
            if task.status == TaskStatus.PENDING
        ]
        assert len(pending) == 1
        delay = pending[0].execute_at - datetime.now(tz=UTC)
        assert LATE_QUESTION_EMAIL_DELAY - timedelta(minutes=5) < delay
        assert delay < LATE_QUESTION_EMAIL_DELAY + timedelta(minutes=5)

        with patch(
            "ring.tasks.crud.late_question_email_task.send_email",
            return_value="message-id",
        ) as send_email:
            task = _run_pending(db_session, letter)

        assert task.status == TaskStatus.COMPLETED
        send_email.assert_called_once()
        draft = send_email.call_args.args[0]
        assert draft.destination["ToAddresses"] == [responder.email]
        assert current_user.email not in draft.destination["ToAddresses"]
        assert silent.email not in draft.destination["ToAddresses"]
        text = draft.message["Body"]["Text"]["Data"]
        html_body = draft.message["Body"]["Html"]["Data"]
        subject = draft.message["Subject"]["Data"]
        assert text.index("First late question?") < text.index(
            "Second late question?"
        )
        assert "First late question?" in html_body
        assert "Second late question?" in html_body
        assert subject == "Ring: New questions on Spring"
        assert "badge" not in html_body.lower()
        assert letter.last_late_question_email_at is not None

    def test_later_question_waits_for_the_window(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: UserFactory,
    ) -> None:
        """A question added after the email waits out the 24h window."""
        responder = UserFactory.create()
        group = GroupFactory.create(
            admin=current_user,
            members=[current_user, responder],
        )
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            title="Spring",
            send_at=datetime.now(tz=UTC) + timedelta(days=3),
        )
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=responder)
        db_session.commit()
        added = _add_question(
            authenticated_client,
            letter,
            "Already emailed?",
            current_user.api_identifier,
        )
        assert added.status_code == 200
        with patch(
            "ring.tasks.crud.late_question_email_task.send_email",
            return_value="message-id",
        ):
            _run_pending(db_session, letter)

        follow_up = _add_question(
            authenticated_client,
            letter,
            "After the email?",
            current_user.api_identifier,
        )
        assert follow_up.status_code == 200
        # The test session shares one transaction, so Cockroach now() is
        # identical for every row. Production requests do not. Move the
        # follow-up strictly after the watermark.
        db_session.expire(letter, ["questions"])
        follow_up_question = next(
            item
            for item in letter.questions
            if item.question_text == "After the email?"
        )
        follow_up_question.created_at = datetime.now(tz=UTC)
        db_session.commit()
        pending = [
            task
            for task in _late_question_tasks(db_session, letter)
            if task.status == TaskStatus.PENDING
        ]
        assert len(pending) == 1
        assert (
            pending[0].execute_at
            >= letter.last_late_question_email_at
            + LATE_QUESTION_EMAIL_WINDOW
            - timedelta(seconds=1)
        )
        assert pending[0].execute_at > datetime.now(tz=UTC) + timedelta(
            hours=20
        )

        with patch(
            "ring.tasks.crud.late_question_email_task.send_email",
            return_value="message-id",
        ) as send_email:
            JOB_REGISTRY["send_late_question_email"].job_function(
                db_session,
                pending[0].id,
                **pending[0].arguments,
            )
        send_email.assert_called_once()
        text = send_email.call_args.args[0].message["Body"]["Text"]["Data"]
        assert "After the email?" in text
        assert "Already emailed?" not in text

    def test_deleted_question_is_left_out(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: UserFactory,
    ) -> None:
        responder = UserFactory.create()
        group = GroupFactory.create(
            admin=current_user,
            members=[current_user, responder],
        )
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            title="Spring",
            send_at=datetime.now(tz=UTC) + timedelta(days=3),
        )
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=responder)
        db_session.commit()
        kept = _add_question(
            authenticated_client,
            letter,
            "Keep this question?",
            current_user.api_identifier,
        )
        removed = _add_question(
            authenticated_client,
            letter,
            "Delete this question?",
            current_user.api_identifier,
        )
        assert kept.status_code == 200
        assert removed.status_code == 200
        db_session.expire(letter, ["questions"])
        doomed = next(
            item
            for item in letter.questions
            if item.question_text == "Delete this question?"
        )
        delete_question(db_session, doomed)
        db_session.commit()

        with patch(
            "ring.tasks.crud.late_question_email_task.send_email",
            return_value="message-id",
        ) as send_email:
            _run_pending(db_session, letter)

        send_email.assert_called_once()
        text = send_email.call_args.args[0].message["Body"]["Text"]["Data"]
        assert "Keep this question?" in text
        assert "Delete this question?" not in text

    def test_no_email_when_every_late_question_was_deleted(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: UserFactory,
    ) -> None:
        responder = UserFactory.create()
        group = GroupFactory.create(
            admin=current_user,
            members=[current_user, responder],
        )
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            title="Spring",
            send_at=datetime.now(tz=UTC) + timedelta(days=3),
        )
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=responder)
        db_session.commit()
        added = _add_question(
            authenticated_client,
            letter,
            "Gone?",
            current_user.api_identifier,
        )
        assert added.status_code == 200
        db_session.expire(letter, ["questions"])
        doomed = next(
            item for item in letter.questions if item.question_text == "Gone?"
        )
        delete_question(db_session, doomed)
        db_session.commit()

        with patch(
            "ring.tasks.crud.late_question_email_task.send_email",
            return_value="message-id",
        ) as send_email:
            task = _run_pending(db_session, letter)

        send_email.assert_not_called()
        assert task.status == TaskStatus.COMPLETED
        assert letter.last_late_question_email_at is None

    def test_queued_email_is_dropped_inside_the_cutoff(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: UserFactory,
    ) -> None:
        responder = UserFactory.create()
        group = GroupFactory.create(
            admin=current_user,
            members=[current_user, responder],
        )
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            title="Spring",
            send_at=datetime.now(tz=UTC) + timedelta(days=3),
        )
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=responder)
        db_session.commit()
        added = _add_question(
            authenticated_client,
            letter,
            "Too close?",
            current_user.api_identifier,
        )
        assert added.status_code == 200
        letter.send_at = datetime.now(tz=UTC) + timedelta(hours=12)
        db_session.commit()

        with patch(
            "ring.tasks.crud.late_question_email_task.send_email",
            return_value="message-id",
        ) as send_email:
            task = _run_pending(db_session, letter)

        send_email.assert_not_called()
        assert task.status == TaskStatus.COMPLETED
        assert letter.last_late_question_email_at is None

    def test_queued_email_is_dropped_after_the_letter_is_sent(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: UserFactory,
    ) -> None:
        responder = UserFactory.create()
        group = GroupFactory.create(
            admin=current_user,
            members=[current_user, responder],
        )
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            title="Spring",
            send_at=datetime.now(tz=UTC) + timedelta(days=3),
        )
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=responder)
        db_session.commit()
        added = _add_question(
            authenticated_client,
            letter,
            "Already sent?",
            current_user.api_identifier,
        )
        assert added.status_code == 200
        letter.status = LetterStatus.SENT
        db_session.commit()

        with patch(
            "ring.tasks.crud.late_question_email_task.send_email",
            return_value="message-id",
        ) as send_email:
            task = _run_pending(db_session, letter)

        send_email.assert_not_called()
        assert task.status == TaskStatus.COMPLETED
        assert letter.last_late_question_email_at is None

    def test_upcoming_add_schedules_nothing(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: UserFactory,
    ) -> None:
        responder = UserFactory.create()
        group = GroupFactory.create(
            admin=current_user,
            members=[current_user, responder],
        )
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.UPCOMING,
            title="Spring",
            send_at=datetime.now(tz=UTC) + timedelta(days=10),
        )
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=responder)
        db_session.commit()
        added = _add_question(
            authenticated_client,
            letter,
            "Not late?",
            current_user.api_identifier,
        )
        assert added.status_code == 200
        assert _late_question_tasks(db_session, letter) == []

    def test_non_responder_is_not_emailed_when_nobody_else_replied(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: UserFactory,
    ) -> None:
        silent = UserFactory.create()
        group = GroupFactory.create(
            admin=current_user,
            members=[current_user, silent],
        )
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            title="Spring",
            send_at=datetime.now(tz=UTC) + timedelta(days=3),
        )
        db_session.commit()
        added = _add_question(
            authenticated_client,
            letter,
            "Anyone there?",
            current_user.api_identifier,
        )
        assert added.status_code == 200
        assert len(_late_question_tasks(db_session, letter)) == 1

        with patch(
            "ring.tasks.crud.late_question_email_task.send_email",
            return_value="message-id",
        ) as send_email:
            _run_pending(db_session, letter)

        send_email.assert_not_called()

    def test_authors_are_left_off_their_own_questions(
        self,
        authenticated_client: TestClient,
        get_client_for_user,
        db_session: Session,
        current_user: UserFactory,
    ) -> None:
        """Each responder gets one email, without questions they authored."""
        other_author = UserFactory.create()
        bystander = UserFactory.create()
        group = GroupFactory.create(
            admin=current_user,
            members=[current_user, other_author, bystander],
        )
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            title="Spring",
            send_at=datetime.now(tz=UTC) + timedelta(days=3),
        )
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=current_user)
        ResponseFactory.create(question=question, participant=other_author)
        ResponseFactory.create(question=question, participant=bystander)
        db_session.commit()
        first = _add_question(
            authenticated_client,
            letter,
            "From the admin?",
            current_user.api_identifier,
        )
        # The server records the signed-in caller as the author.
        second = _add_question(
            get_client_for_user(other_author),
            letter,
            "From the other author?",
            other_author.api_identifier,
        )
        assert first.status_code == 200
        assert second.status_code == 200
        assert (
            len(
                [
                    task
                    for task in _late_question_tasks(db_session, letter)
                    if task.status == TaskStatus.PENDING
                ]
            )
            == 1
        )

        with patch(
            "ring.tasks.crud.late_question_email_task.send_email",
            return_value="message-id",
        ) as send_email:
            _run_pending(db_session, letter)

        bodies = {
            tuple(call.args[0].destination["ToAddresses"]): call.args[
                0
            ].message["Body"]["Text"]["Data"]
            for call in send_email.call_args_list
        }
        assert set(bodies) == {
            (other_author.email,),
            (bystander.email,),
            (current_user.email,),
        }
        assert "From the other author?" in bodies[(current_user.email,)]
        assert "From the admin?" not in bodies[(current_user.email,)]
        assert "From the admin?" in bodies[(other_author.email,)]
        assert "From the other author?" not in bodies[(other_author.email,)]
        assert "From the admin?" in bodies[(bystander.email,)]
        assert "From the other author?" in bodies[(bystander.email,)]

    def test_partial_failure_retries_only_the_recipients_who_missed_it(
        self,
        authenticated_client: TestClient,
        get_client_for_user,
        db_session: Session,
        current_user: UserFactory,
    ) -> None:
        other = UserFactory.create()
        group = GroupFactory.create(
            admin=current_user,
            members=[current_user, other],
        )
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            title="Spring",
            send_at=datetime.now(tz=UTC) + timedelta(days=3),
        )
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=current_user)
        ResponseFactory.create(question=question, participant=other)
        db_session.commit()
        first = _add_question(
            authenticated_client,
            letter,
            "From the admin?",
            current_user.api_identifier,
        )
        # The server records the signed-in caller as the author.
        second = _add_question(
            get_client_for_user(other),
            letter,
            "From the other author?",
            other.api_identifier,
        )
        assert first.status_code == 200
        assert second.status_code == 200

        def reject_the_second_batch(draft):
            if reject_the_second_batch.calls:
                return None
            reject_the_second_batch.calls.append(draft)
            return "message-id"

        reject_the_second_batch.calls = []
        with patch(
            "ring.tasks.crud.late_question_email_task.send_email",
            side_effect=reject_the_second_batch,
        ) as send_email:
            task = _run_pending(db_session, letter)

        assert task.status == TaskStatus.PENDING
        assert int(task.arguments["attempt"]) == 2
        assert letter.last_late_question_email_at is None
        assert send_email.call_count == 2
        delivered = set(
            send_email.call_args_list[0].args[0].destination["ToAddresses"]
        )
        missed = set(
            send_email.call_args_list[1].args[0].destination["ToAddresses"]
        )
        assert delivered.isdisjoint(missed)

        with patch(
            "ring.tasks.crud.late_question_email_task.send_email",
            return_value="message-id",
        ) as retry_send:
            task = _run_pending(db_session, letter)

        assert task.status == TaskStatus.COMPLETED
        retry_send.assert_called_once()
        retried = set(retry_send.call_args.args[0].destination["ToAddresses"])
        assert retried == missed
        assert retried.isdisjoint(delivered)
        assert letter.last_late_question_email_at is not None

    def test_rejected_send_is_retried_without_a_new_question(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: UserFactory,
    ) -> None:
        responder = UserFactory.create()
        group = GroupFactory.create(
            admin=current_user,
            members=[current_user, responder],
        )
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            title="Spring",
            send_at=datetime.now(tz=UTC) + timedelta(days=3),
        )
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=responder)
        db_session.commit()
        added = _add_question(
            authenticated_client,
            letter,
            "Only question?",
            current_user.api_identifier,
        )
        assert added.status_code == 200
        question_count = len(letter.questions)

        with patch(
            "ring.tasks.crud.late_question_email_task.send_email",
            return_value=None,
        ):
            task = _run_pending(db_session, letter)

        assert task.status == TaskStatus.PENDING
        assert int(task.arguments["attempt"]) == 2
        wait = task.execute_at - datetime.now(tz=UTC)
        assert wait > LATE_QUESTION_EMAIL_RETRY_BACKOFF - timedelta(seconds=5)
        assert wait < LATE_QUESTION_EMAIL_RETRY_BACKOFF + timedelta(minutes=1)
        db_session.expire(letter, ["questions"])
        assert len(letter.questions) == question_count

        with patch(
            "ring.tasks.crud.late_question_email_task.send_email",
            return_value="message-id",
        ) as send_email:
            task = _run_pending(db_session, letter)

        assert task.status == TaskStatus.COMPLETED
        send_email.assert_called_once()
        assert send_email.call_args.args[0].destination["ToAddresses"] == [
            responder.email
        ]
        assert (
            "Only question?"
            in (send_email.call_args.args[0].message["Body"]["Text"]["Data"])
        )
        assert letter.last_late_question_email_at is not None

    def test_retry_stops_inside_the_cutoff(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: UserFactory,
    ) -> None:
        responder = UserFactory.create()
        group = GroupFactory.create(
            admin=current_user,
            members=[current_user, responder],
        )
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            title="Spring",
            send_at=datetime.now(tz=UTC) + timedelta(days=3),
        )
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=responder)
        db_session.commit()
        added = _add_question(
            authenticated_client,
            letter,
            "Too close?",
            current_user.api_identifier,
        )
        assert added.status_code == 200
        with patch(
            "ring.tasks.crud.late_question_email_task.send_email",
            return_value=None,
        ):
            _run_pending(db_session, letter)
        letter.send_at = datetime.now(tz=UTC) + timedelta(hours=12)
        db_session.commit()

        with patch(
            "ring.tasks.crud.late_question_email_task.send_email",
            return_value="message-id",
        ) as send_email:
            task = _run_pending(db_session, letter)

        send_email.assert_not_called()
        assert task.status == TaskStatus.COMPLETED
        assert _pending_count(db_session, letter) == 0

    def test_retry_stops_after_the_letter_is_sent(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: UserFactory,
    ) -> None:
        responder = UserFactory.create()
        group = GroupFactory.create(
            admin=current_user,
            members=[current_user, responder],
        )
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            title="Spring",
            send_at=datetime.now(tz=UTC) + timedelta(days=3),
        )
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=responder)
        db_session.commit()
        added = _add_question(
            authenticated_client,
            letter,
            "Already sent?",
            current_user.api_identifier,
        )
        assert added.status_code == 200
        with patch(
            "ring.tasks.crud.late_question_email_task.send_email",
            return_value=None,
        ):
            _run_pending(db_session, letter)
        letter.status = LetterStatus.SENT
        db_session.commit()

        with patch(
            "ring.tasks.crud.late_question_email_task.send_email",
            return_value="message-id",
        ) as send_email:
            task = _run_pending(db_session, letter)

        send_email.assert_not_called()
        assert task.status == TaskStatus.COMPLETED
        assert _pending_count(db_session, letter) == 0

    def test_retry_stops_when_the_attempt_cap_is_reached(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: UserFactory,
    ) -> None:
        responder = UserFactory.create()
        group = GroupFactory.create(
            admin=current_user,
            members=[current_user, responder],
        )
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            title="Spring",
            send_at=datetime.now(tz=UTC) + timedelta(days=3),
        )
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=responder)
        db_session.commit()
        added = _add_question(
            authenticated_client,
            letter,
            "Never accepted?",
            current_user.api_identifier,
        )
        assert added.status_code == 200

        with patch(
            "ring.tasks.crud.late_question_email_task.send_email",
            return_value=None,
        ) as send_email:
            task = None
            for _ in range(LATE_QUESTION_EMAIL_MAX_ATTEMPTS):
                task = _run_pending(db_session, letter)

        assert send_email.call_count == LATE_QUESTION_EMAIL_MAX_ATTEMPTS
        assert task is not None
        assert task.status == TaskStatus.FAILED
        assert "3 attempts" in task.message
        assert _pending_count(db_session, letter) == 0
        assert letter.last_late_question_email_at is None


def _pending_count(db: Session, letter: Letter) -> int:
    return len(
        [
            task
            for task in _late_question_tasks(db, letter)
            if task.status == TaskStatus.PENDING
        ]
    )


class TestConstructLateQuestionEmail:
    def test_plain_copy_has_no_late_badge(self, db_session: Session) -> None:
        question = QuestionFactory.create(question_text="What is new?")
        question.author = UserFactory.create(name="Ada Lovelace")
        db_session.commit()
        letter = question.letter
        draft = construct_late_question_email(
            ["ada@example.com"],
            "Family",
            letter.api_identifier,
            "Spring",
            [question],
        )
        subject = draft.message["Subject"]["Data"]
        text = draft.message["Body"]["Text"]["Data"]
        html_body = draft.message["Body"]["Html"]["Data"]
        assert subject == "Ring: New question on Spring"
        assert "Ada Lovelace added a question to Spring in Family." in text
        assert "What is new?" in text
        assert app_url(f"loops/{letter.api_identifier}") in text
        assert "Late" not in subject
        assert "Late" not in text
        assert "Late" not in html_body
        assert draft.destination["ToAddresses"] == ["ada@example.com"]

    def test_escapes_question_text(self, db_session: Session) -> None:
        question = QuestionFactory.create(question_text="a < b & c")
        db_session.commit()
        draft = construct_late_question_email(
            ["ada@example.com"],
            "Family",
            question.letter.api_identifier,
            "Spring",
            [question],
        )
        html_body = draft.message["Body"]["Html"]["Data"]
        text = draft.message["Body"]["Text"]["Data"]
        assert "a &lt; b &amp; c" in html_body
        assert "a < b & c" in text
        assert "a < b & c" not in html_body
