"""Authz coverage for response and question response mutations.

The UI only lets a member edit their own answer. These tests pin matching API
gates so a caller with a response or question id cannot mutate another
member's content — or touch resources in a group they do not belong to.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.letters.constants import LetterStatus
from ring.parties.models.user_model import User
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.letters.response_factory import ResponseFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory


class TestResponseAuthz:
    def test_non_member_cannot_edit_response(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        response = ResponseFactory.create()
        db_session.commit()
        original_text = response.response_text

        rv = authenticated_client.post(
            f"/responses/response/{response.api_identifier}:edit_response",
            json={"response_text": "hijacked"},
        )

        assert rv.status_code == 403
        assert rv.json()["detail"] == (
            "Not authorized to access this resource"
        )
        db_session.refresh(response)
        assert response.response_text == original_text

    def test_other_member_cannot_edit_response(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        admin = UserFactory.create()
        owner = UserFactory.create()
        group = GroupFactory.create(
            admin=admin, members=[admin, owner, current_user]
        )
        letter = LetterFactory.create(
            group=group, status=LetterStatus.IN_PROGRESS
        )
        question = QuestionFactory.create(letter=letter)
        response = ResponseFactory.create(
            question=question, participant=owner, response_text="mine"
        )
        db_session.commit()

        rv = authenticated_client.post(
            f"/responses/response/{response.api_identifier}:edit_response",
            json={"response_text": "hijacked"},
        )

        assert rv.status_code == 403
        assert rv.json()["detail"] == (
            "Only the response author or group admin can modify this response"
        )
        db_session.refresh(response)
        assert response.response_text == "mine"

    def test_owner_can_edit_own_response(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin, current_user])
        letter = LetterFactory.create(
            group=group, status=LetterStatus.IN_PROGRESS
        )
        question = QuestionFactory.create(letter=letter)
        response = ResponseFactory.create(
            question=question,
            participant=current_user,
            response_text="draft",
        )
        db_session.commit()

        rv = authenticated_client.post(
            f"/responses/response/{response.api_identifier}:edit_response",
            json={"response_text": "updated"},
        )

        assert rv.status_code == 200
        assert rv.json()["response_text"] == "updated"
        db_session.refresh(response)
        assert response.response_text == "updated"

    def test_non_member_cannot_delete_image(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        response = ResponseFactory.create()
        db_session.commit()

        rv = authenticated_client.delete(
            f"/responses/response/{response.api_identifier}:delete_image",
            params={"s3_url": "https://example.com/missing.png"},
        )

        assert rv.status_code == 403
        assert rv.json()["detail"] == (
            "Not authorized to access this resource"
        )


class TestQuestionResponseAuthz:
    def test_non_member_cannot_upsert_response(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        question = QuestionFactory.create()
        db_session.commit()

        rv = authenticated_client.post(
            f"/questions/question/{question.api_identifier}:upsert_response",
            json={
                "response_text": "should not land",
                "participant_api_identifier": current_user.api_identifier,
            },
        )

        assert rv.status_code == 403
        assert rv.json()["detail"] == (
            "Not authorized to access this resource"
        )
        db_session.refresh(question)
        assert all(
            r.response_text != "should not land" for r in question.responses
        )

    def test_other_member_cannot_upsert_another_participants_response(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        admin = UserFactory.create()
        owner = UserFactory.create()
        group = GroupFactory.create(
            admin=admin, members=[admin, owner, current_user]
        )
        letter = LetterFactory.create(
            group=group, status=LetterStatus.IN_PROGRESS
        )
        question = QuestionFactory.create(letter=letter)
        response = ResponseFactory.create(
            question=question, participant=owner, response_text="owner text"
        )
        db_session.commit()

        rv = authenticated_client.post(
            f"/questions/question/{question.api_identifier}:upsert_response",
            json={
                "response_text": "hijacked",
                "participant_api_identifier": owner.api_identifier,
            },
        )

        assert rv.status_code == 403
        assert rv.json()["detail"] == (
            "Only the response author or group admin can modify this response"
        )
        db_session.refresh(response)
        assert response.response_text == "owner text"

    def test_member_can_upsert_own_response(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin, current_user])
        letter = LetterFactory.create(
            group=group, status=LetterStatus.IN_PROGRESS
        )
        question = QuestionFactory.create(letter=letter)
        db_session.commit()

        rv = authenticated_client.post(
            f"/questions/question/{question.api_identifier}:upsert_response",
            json={
                "response_text": "my answer",
                "participant_api_identifier": current_user.api_identifier,
            },
        )

        assert rv.status_code == 200
        db_session.refresh(question)
        assert any(
            r.participant == current_user and r.response_text == "my answer"
            for r in question.responses
        )

    def test_non_member_cannot_delete_question(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        question = QuestionFactory.create(
            letter=LetterFactory.create(status=LetterStatus.UPCOMING)
        )
        db_session.commit()

        rv = authenticated_client.delete(
            f"/questions/question/{question.api_identifier}"
        )

        assert rv.status_code == 403
        assert rv.json()["detail"] == (
            "Not authorized to access this resource"
        )
        db_session.refresh(question)
        assert question.id is not None
