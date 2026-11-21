"""Admin send-now: bypass the responder gate without double-sending."""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from ring.letters.constants import LetterStatus
from ring.letters.crud import letter as letter_crud
from ring.letters.models.letter_model import Letter
from ring.parties.models.user_model import User
from ring.tasks.crud import task as task_crud
from ring.tasks.models.task_model import Task, TaskStatus, TaskType
from ring.tests.factories.base_factory import ALL_FACTORIES
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.letters.response_factory import ResponseFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory
from ring.tests.lib.utils import (
    email_draft_recipients,
    is_waiting_response_email,
)

_ONLY_IN_PROGRESS = "Only an in-progress letter can be sent now"


def _bind_factories(session: Session) -> None:
    for factory in ALL_FACTORIES:
        factory._meta.sqlalchemy_session = session


def _send_now_path(api_identifier: str) -> str:
    return f"/letters/letter/{api_identifier}:send_now"


def _below_threshold_letter(
    db_session: Session,
    *,
    admin: User,
) -> tuple[Letter, list[User]]:
    """Four members, one response: the scheduled send would defer."""
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
    return letter, members


class TestSendLetterNow:
    def test_admin_sends_now_below_threshold(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        letter, members = _below_threshold_letter(
            db_session, admin=current_user
        )
        group = letter.group
        send_at = letter.send_at

        with patch(
            "ring.letters.crud.letter.send_email",
            return_value="message-id",
        ) as mock_send_email:
            response = authenticated_client.post(
                _send_now_path(letter.api_identifier)
            )

        assert response.status_code == 200
        body = response.json()
        assert body["api_identifier"] == letter.api_identifier
        assert body["status"] == LetterStatus.SENT
        mock_send_email.assert_called_once()
        assert not is_waiting_response_email(mock_send_email)
        assert set(email_draft_recipients(mock_send_email)) == {
            member.email for member in members
        }
        db_session.refresh(letter)
        assert letter.status == LetterStatus.SENT
        assert letter.send_at == send_at
        assert letter.automatic_send_deferral_count == 0
        assert len(group.upcoming_letters) == 1
        assert group.upcoming_letters[0].send_at == send_at + timedelta(
            days=group.cycle_length
        )

    def test_non_admin_member_cannot_send_now(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        admin = UserFactory.create()
        members = [admin, current_user] + [
            UserFactory.create() for _ in range(2)
        ]
        group = GroupFactory.create(admin=admin, members=members)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=datetime.now(tz=UTC) - timedelta(minutes=1),
        )
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=members[0])
        db_session.commit()

        with patch(
            "ring.letters.crud.letter.send_email",
            return_value="message-id",
        ) as mock_send_email:
            response = authenticated_client.post(
                _send_now_path(letter.api_identifier)
            )

        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Only the group admin can send this letter now"
        )
        mock_send_email.assert_not_called()
        db_session.refresh(letter)
        assert letter.status == LetterStatus.IN_PROGRESS

    def test_second_send_now_does_not_resend(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        letter, _members = _below_threshold_letter(
            db_session, admin=current_user
        )

        with patch(
            "ring.letters.crud.letter.send_email",
            return_value="message-id",
        ) as mock_send_email:
            first = authenticated_client.post(
                _send_now_path(letter.api_identifier)
            )
            second = authenticated_client.post(
                _send_now_path(letter.api_identifier)
            )

        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json()["status"] == LetterStatus.SENT
        assert second.json()["status"] == LetterStatus.SENT
        mock_send_email.assert_called_once()
        db_session.refresh(letter)
        assert letter.status == LetterStatus.SENT
        assert len(letter.group.upcoming_letters) == 1

    def test_upcoming_letter_cannot_be_sent_now(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        letter = LetterFactory.create(
            group=GroupFactory.create(admin=current_user),
            status=LetterStatus.UPCOMING,
        )
        db_session.commit()

        response = authenticated_client.post(
            _send_now_path(letter.api_identifier)
        )

        assert response.status_code == 400
        assert response.json()["detail"] == _ONLY_IN_PROGRESS
        db_session.refresh(letter)
        assert letter.status == LetterStatus.UPCOMING

    def test_rejected_email_leaves_letter_in_progress(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        letter, _members = _below_threshold_letter(
            db_session, admin=current_user
        )

        with patch(
            "ring.letters.crud.letter.send_email",
            return_value=None,
        ) as mock_send_email:
            response = authenticated_client.post(
                _send_now_path(letter.api_identifier)
            )

        assert response.status_code == 400
        assert response.json()["detail"] == "Letter email was not accepted"
        mock_send_email.assert_called_once()
        db_session.refresh(letter)
        assert letter.status == LetterStatus.IN_PROGRESS
        assert letter.group.upcoming_letters == []

    def test_edit_letter_crud_rejects_sent_status(
        self,
        db_session: Session,
    ) -> None:
        letter = LetterFactory.create(status=LetterStatus.IN_PROGRESS)
        db_session.commit()

        with pytest.raises(
            ValueError, match="Cannot mark a letter sent by editing it"
        ):
            letter_crud.edit_letter(
                db_session, letter, status=LetterStatus.SENT
            )
        assert letter.status == LetterStatus.IN_PROGRESS

    def test_scheduled_task_is_noop_after_send_now(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        """The due send task does not email a letter send-now already sent."""
        admin = current_user
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
        send_task = db_session.scalars(
            select(Task).where(
                Task.schedule_id == group.schedule.id,
                Task.type == TaskType.SEND_EMAIL,
                Task.arguments == {"letter_id": letter.id},
            )
        ).one()

        with patch(
            "ring.letters.crud.letter.send_email",
            return_value="message-id",
        ) as mock_send_email:
            response = authenticated_client.post(
                _send_now_path(letter.api_identifier)
            )
            assert response.status_code == 200
            task_crud.execute_send_email_task(
                db_session, send_task, letter_id=letter.id
            )

        mock_send_email.assert_called_once()
        db_session.refresh(letter)
        assert letter.status == LetterStatus.SENT
        assert len(group.upcoming_letters) == 1


def _purge_committed_group(
    session: Session, group_id: int, user_ids: list[int]
) -> None:
    params = {"group_id": group_id}
    session.execute(
        text(
            """
            DELETE FROM hybrid_search_document
            WHERE id IN (
                SELECT hybrid_search_document_id
                FROM hybrid_search_document_association
                WHERE model_api_identifier IN (
                    SELECT api_identifier FROM letter
                    WHERE group_id = :group_id
                    UNION
                    SELECT question.api_identifier
                    FROM question
                    JOIN letter ON letter.id = question.letter_id
                    WHERE letter.group_id = :group_id
                )
            )
            """
        ),
        params,
    )
    session.execute(
        text(
            """
            DELETE FROM response
            WHERE question_id IN (
                SELECT question.id FROM question
                JOIN letter ON letter.id = question.letter_id
                WHERE letter.group_id = :group_id
            )
            """
        ),
        params,
    )
    session.execute(
        text(
            """
            DELETE FROM question
            WHERE letter_id IN (
                SELECT id FROM letter WHERE group_id = :group_id
            )
            """
        ),
        params,
    )
    session.execute(
        text(
            """
            DELETE FROM letter_to_user_assocation
            WHERE letter_id IN (
                SELECT id FROM letter WHERE group_id = :group_id
            )
            """
        ),
        params,
    )
    session.execute(
        text(
            """
            DELETE FROM task
            WHERE schedule_id IN (
                SELECT id FROM schedule WHERE group_id = :group_id
            )
            """
        ),
        params,
    )
    session.execute(
        text("DELETE FROM letter WHERE group_id = :group_id"),
        params,
    )
    session.execute(
        text("DELETE FROM schedule WHERE group_id = :group_id"),
        params,
    )
    session.execute(
        text("DELETE FROM user_group_assocation WHERE group_id = :group_id"),
        params,
    )
    session.execute(
        text("DELETE FROM group_key_value WHERE group_id = :group_id"),
        params,
    )
    session.execute(
        text("DELETE FROM default_question WHERE group_id = :group_id"),
        params,
    )
    session.execute(
        text('DELETE FROM "group" WHERE id = :group_id'),
        params,
    )
    for user_id in user_ids:
        session.execute(
            text('DELETE FROM "user" WHERE id = :user_id'),
            {"user_id": user_id},
        )
    session.commit()


def _overlap_send_now(
    db_session: Session,
    db_engine: Engine,
    overlap: Callable[[Session, int, int], None],
    *,
    fail_send_task: bool,
) -> None:
    """Hold the letter lock inside send-now while ``overlap`` also runs.

    The letter meets the responder threshold and is due, so the overlap
    would email it too unless it locks and sees SENT. ``fail_send_task``
    makes postpend the owner; a live task makes the scheduled send the owner.
    """
    setup = Session(bind=db_engine)
    _bind_factories(setup)
    group_id: int | None = None
    user_ids: list[int] = []
    try:
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
        setup.commit()
        send_task = setup.scalars(
            select(Task).where(
                Task.schedule_id == group.schedule.id,
                Task.type == TaskType.SEND_EMAIL,
                Task.arguments == {"letter_id": letter.id},
            )
        ).one()
        if fail_send_task:
            send_task.status = TaskStatus.FAILED
            setup.commit()
        group_id = group.id
        user_ids = [member.id for member in members]
        letter_id = letter.id
        task_id = send_task.id
    finally:
        setup.close()
        _bind_factories(db_session)

    assert group_id is not None
    errors: list[BaseException] = []
    calls = {"n": 0}
    call_lock = threading.Lock()
    in_send = threading.Event()
    release_send = threading.Event()
    overlap_started = threading.Event()

    def blocking_send(_draft: object) -> str:
        with call_lock:
            calls["n"] += 1
        in_send.set()
        assert release_send.wait(timeout=10)
        return "message-id"

    def run_send_now() -> None:
        session = Session(bind=db_engine)
        try:
            locked = session.get(Letter, letter_id)
            assert locked is not None
            letter_crud.send_letter_now(session, locked)
            session.commit()
        except BaseException as exc:
            session.rollback()
            errors.append(exc)
        finally:
            session.close()

    def run_overlap() -> None:
        overlap_started.set()
        session = Session(bind=db_engine)
        try:
            overlap(session, letter_id, task_id)
        except BaseException as exc:
            session.rollback()
            errors.append(exc)
        finally:
            session.close()

    send_now_thread = threading.Thread(target=run_send_now)
    overlap_thread = threading.Thread(target=run_overlap)
    try:
        with patch(
            "ring.letters.crud.letter.send_email",
            side_effect=blocking_send,
        ):
            send_now_thread.start()
            assert in_send.wait(timeout=10)
            overlap_thread.start()
            assert overlap_started.wait(timeout=10)
            deadline = time.monotonic() + 2
            while (
                time.monotonic() < deadline
                and overlap_thread.is_alive()
                and calls["n"] == 1
            ):
                time.sleep(0.05)
            assert calls["n"] == 1
            assert overlap_thread.is_alive()
            release_send.set()
            send_now_thread.join(timeout=10)
            overlap_thread.join(timeout=10)
            check = Session(bind=db_engine)
            try:
                sent = check.get(Letter, letter_id)
                assert sent is not None
                assert sent.status == LetterStatus.SENT
                assert len(sent.group.upcoming_letters) == 1
            finally:
                check.close()
    finally:
        release_send.set()
        send_now_thread.join(timeout=10)
        overlap_thread.join(timeout=10)
        cleanup = Session(bind=db_engine)
        try:
            _purge_committed_group(cleanup, group_id, user_ids)
        finally:
            cleanup.close()

    assert errors == []
    assert not send_now_thread.is_alive()
    assert not overlap_thread.is_alive()
    assert calls["n"] == 1


class TestSendNowRace:
    def test_send_now_and_scheduled_task_send_once(
        self,
        db_session: Session,
        db_engine: Engine,
    ) -> None:
        """One email when send-now holds the row lock across the send."""

        def run_task(session: Session, letter_id: int, task_id: int) -> None:
            send_task = session.get(Task, task_id)
            assert send_task is not None
            task_crud.execute_send_email_task(
                session, send_task, letter_id=letter_id
            )

        _overlap_send_now(
            db_session, db_engine, run_task, fail_send_task=False
        )

    def test_send_now_and_postpend_send_once_when_task_failed(
        self,
        db_session: Session,
        db_engine: Engine,
    ) -> None:
        """Postpend does not email a letter send-now already locked."""

        def run_postpend(
            session: Session, letter_id: int, _task_id: int
        ) -> None:
            letter_crud.postpend_upcoming_letters_with_session(
                session, [letter_id]
            )

        _overlap_send_now(
            db_session, db_engine, run_postpend, fail_send_task=True
        )
