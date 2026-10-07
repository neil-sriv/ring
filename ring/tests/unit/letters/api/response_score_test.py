"""Tests for scoring a response through System One.

The LLM client is mocked. These tests do not call TypeSafe.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.letters.constants import LetterStatus
from ring.letters.crud import response_score as response_score_crud
from ring.parties.models.user_model import User
from ring.systemone.client import SystemOneClientError
from ring.systemone.schemas import ScoreAnswer, SystemOneResponse, Usage
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.letters.response_factory import ResponseFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory

_LEGEND = {
    "0": "Your draft does not answer the prompt",
    "1": "Your draft mentions the prompt without answering it",
    "2": "Your draft answers the prompt",
    "3": "Your draft answers the prompt with specific detail",
}


def _member_response(
    user: User,
    *,
    response_text: str = "I baked bread on Sunday.",
):
    group = GroupFactory.create(admin=user)
    letter = LetterFactory.create(group=group)
    question = QuestionFactory.create(
        letter=letter,
        question_text="What did you do this weekend?",
    )
    return ResponseFactory.create(
        question=question,
        participant=user,
        response_text=response_text,
    )


def _scored(*_args, **_kwargs) -> SystemOneResponse:
    return SystemOneResponse(
        model="ring-llm-wrapper:jev-latest",
        answers={
            "completeness": ScoreAnswer(
                score=2.1,
                legend=_LEGEND,
                probabilities={"2": 0.9, "3": 0.1},
                confidence=0.8,
            )
        },
        usage=Usage(),
    )


class TestScoreResponseAPI:
    def test_score_response(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
        monkeypatch,
    ) -> None:
        response = _member_response(current_user)
        db_session.commit()
        seen: dict = {}

        def capture(request):
            seen["request"] = request
            return _scored()

        monkeypatch.setattr(response_score_crud, "evaluate", capture)

        http = authenticated_client.post(
            f"/responses/response/{response.api_identifier}:score"
        )

        question = seen["request"].questions["completeness"]
        assert question.type == "score"
        assert question.instructions == "Does this draft answer the prompt?"
        assert question.criteria[2] == "Your draft answers the prompt"
        assert seen["request"].state["prompt"] == (
            "What did you do this weekend?"
        )
        assert seen["request"].state["draft"] == "I baked bread on Sunday."
        assert http.status_code == 200
        body = http.json()
        assert body["model"] == "ring-llm-wrapper:jev-latest"
        assert body["score"] == 2.1
        assert body["confidence"] == 0.8
        assert body["legend"]["2"] == "Your draft answers the prompt"

    def test_blank_response_does_not_call_systemone(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
        monkeypatch,
    ) -> None:
        response = _member_response(current_user, response_text="   ")
        db_session.commit()

        def fail_if_called(*_args, **_kwargs):
            raise AssertionError("evaluate should not be called")

        monkeypatch.setattr(response_score_crud, "evaluate", fail_if_called)

        http = authenticated_client.post(
            f"/responses/response/{response.api_identifier}:score"
        )

        assert http.status_code == 400
        assert http.json()["detail"] == "Your draft has no text to check"

    def test_upstream_failure_is_502(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
        monkeypatch,
    ) -> None:
        response = _member_response(current_user)
        db_session.commit()

        def fail(*_args, **_kwargs):
            raise SystemOneClientError(401, "System One request failed")

        monkeypatch.setattr(response_score_crud, "evaluate", fail)

        http = authenticated_client.post(
            f"/responses/response/{response.api_identifier}:score"
        )

        assert http.status_code == 502
        assert http.json()["detail"] == "Could not check this draft"

    def test_other_members_draft_is_forbidden(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
        monkeypatch,
    ) -> None:
        author = UserFactory.create()
        group = GroupFactory.create(
            admin=author, members=[author, current_user]
        )
        letter = LetterFactory.create(group=group)
        question = QuestionFactory.create(letter=letter)
        response = ResponseFactory.create(
            question=question,
            participant=author,
            response_text="Their draft, not mine.",
        )
        db_session.commit()

        def fail_if_called(*_args, **_kwargs):
            raise AssertionError("evaluate should not be called")

        monkeypatch.setattr(response_score_crud, "evaluate", fail_if_called)

        http = authenticated_client.post(
            f"/responses/response/{response.api_identifier}:score"
        )

        assert http.status_code == 403
        assert http.json()["detail"] == "You can only check your own draft"

    def test_sent_letter_is_not_a_draft(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
        monkeypatch,
    ) -> None:
        group = GroupFactory.create(admin=current_user)
        letter = LetterFactory.create(group=group, status=LetterStatus.SENT)
        question = QuestionFactory.create(letter=letter)
        response = ResponseFactory.create(
            question=question,
            participant=current_user,
            response_text="Already sent.",
        )
        db_session.commit()

        def fail_if_called(*_args, **_kwargs):
            raise AssertionError("evaluate should not be called")

        monkeypatch.setattr(response_score_crud, "evaluate", fail_if_called)

        http = authenticated_client.post(
            f"/responses/response/{response.api_identifier}:score"
        )

        assert http.status_code == 400
        assert (
            http.json()["detail"]
            == "You can only check a draft before the letter is sent"
        )

    def test_non_member_is_forbidden(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        other = UserFactory.create()
        response = _member_response(other)
        db_session.commit()

        http = authenticated_client.post(
            f"/responses/response/{response.api_identifier}:score"
        )

        assert http.status_code == 403

    def test_missing_response_is_forbidden(
        self,
        authenticated_client: TestClient,
    ) -> None:
        http = authenticated_client.post(
            "/responses/response/rspn_00000000-0000-0000-0000-"
            "000000000000:score"
        )

        assert http.status_code == 403
