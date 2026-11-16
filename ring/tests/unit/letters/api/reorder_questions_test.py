"""Tests for reordering a letter's questions.

Proposed contract: ``POST /letters/letter/{letter_api_id}:reorder_questions``
with ``{"question_api_identifiers": [...]}`` listing every question on the
letter exactly once, in the new display order. Admin permission on the
letter is required, and only while the letter is UPCOMING or IN_PROGRESS. Returns the
letter with positions 0..n-1 following the submitted order.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.letters.constants import LetterStatus
from ring.letters.models.letter_model import Letter
from ring.letters.models.question_model import Question
from ring.parties.models.user_model import User
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.letters.response_factory import ResponseFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory


def _letter_with_questions(
    admin: User, status: LetterStatus, count: int = 3
) -> tuple[Letter, list[Question]]:
    letter = LetterFactory.create(
        group=GroupFactory.create(admin=admin), status=status
    )
    questions = [QuestionFactory.create(letter=letter) for _ in range(count)]
    return letter, questions


def _reorder(client: TestClient, letter: Letter, question_api_ids: list[str]):
    return client.post(
        f"/letters/letter/{letter.api_identifier}:reorder_questions",
        json={"question_api_identifiers": question_api_ids},
    )


def _displayed_order(client: TestClient, letter: Letter) -> list[str]:
    response = client.get(f"/letters/letter/{letter.api_identifier}")
    assert response.status_code == 200
    questions = sorted(
        response.json()["questions"], key=lambda q: q["position"]
    )
    return [q["api_identifier"] for q in questions]


def _stored_order(db_session: Session, letter: Letter) -> list[str]:
    db_session.expire_all()
    return [
        q.api_identifier
        for q in sorted(letter.questions, key=lambda q: q.position)
    ]


def _api_ids(questions: list[Question]) -> list[str]:
    return [q.api_identifier for q in questions]


class TestReorderQuestions:
    @pytest.mark.parametrize(
        "status", [LetterStatus.UPCOMING, LetterStatus.IN_PROGRESS]
    )
    def test_admin_reorders_live_letter(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
        status: LetterStatus,
    ) -> None:
        letter, (first, second, third) = _letter_with_questions(
            current_user, status
        )
        db_session.commit()
        new_order = _api_ids([third, first, second])

        response = _reorder(authenticated_client, letter, new_order)

        assert response.status_code == 200
        returned = sorted(
            response.json()["questions"], key=lambda q: q["position"]
        )
        assert [q["api_identifier"] for q in returned] == new_order
        assert [q["position"] for q in returned] == [0, 1, 2]
        assert _displayed_order(authenticated_client, letter) == new_order
        assert _stored_order(db_session, letter) == new_order

    def test_sent_letter_rejected(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        letter, questions = _letter_with_questions(
            current_user, LetterStatus.SENT
        )
        db_session.commit()
        original = _api_ids(questions)

        response = _reorder(
            authenticated_client, letter, list(reversed(original))
        )

        assert response.status_code == 400
        assert _stored_order(db_session, letter) == original

    def test_non_admin_member_rejected(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin, current_user])
        letter = LetterFactory.create(
            group=group, status=LetterStatus.UPCOMING
        )
        questions = [QuestionFactory.create(letter=letter) for _ in range(3)]
        db_session.commit()
        original = _api_ids(questions)

        response = _reorder(
            authenticated_client, letter, list(reversed(original))
        )

        assert response.status_code == 403
        assert _stored_order(db_session, letter) == original

    @pytest.mark.parametrize(
        "case", ["missing_question", "duplicate_question", "foreign_question"]
    )
    def test_invalid_order_rejected_and_unchanged(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
        case: str,
    ) -> None:
        letter, (first, second, third) = _letter_with_questions(
            current_user, LetterStatus.UPCOMING
        )
        other_letter_question = QuestionFactory.create(
            letter=LetterFactory.create(
                group=letter.group, status=LetterStatus.SENT
            )
        )
        db_session.commit()
        original = _api_ids([first, second, third])
        payload = {
            "missing_question": _api_ids([third, first]),
            "duplicate_question": _api_ids([third, first, first]),
            "foreign_question": _api_ids(
                [third, first, second, other_letter_question]
            ),
        }[case]

        response = _reorder(authenticated_client, letter, payload)

        assert response.status_code == 400
        assert _stored_order(db_session, letter) == original

    def test_answers_stay_with_their_questions(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        letter, questions = _letter_with_questions(
            current_user, LetterStatus.IN_PROGRESS
        )
        answers = {
            q.api_identifier: ResponseFactory.create(
                question=q, participant=current_user
            ).response_text
            for q in questions
        }
        db_session.commit()

        response = _reorder(
            authenticated_client, letter, list(reversed(_api_ids(questions)))
        )

        assert response.status_code == 200
        read = authenticated_client.get(
            f"/letters/letter/{letter.api_identifier}"
        ).json()
        assert {
            q["api_identifier"]: [r["response_text"] for r in q["responses"]]
            for q in read["questions"]
        } == {api_id: [text] for api_id, text in answers.items()}
