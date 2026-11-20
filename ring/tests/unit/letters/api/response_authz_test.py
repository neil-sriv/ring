"""Authz coverage for response and question response mutations.

The UI only lets a member edit their own answer. These tests pin matching API
gates so a caller with a response or question id cannot mutate another
member's content — or touch resources in a group they do not belong to.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.letters.constants import LetterStatus, LetterType
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

    def test_admin_can_edit_another_members_response(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        member = UserFactory.create()
        group = GroupFactory.create(
            admin=current_user, members=[current_user, member]
        )
        letter = LetterFactory.create(
            group=group, status=LetterStatus.IN_PROGRESS
        )
        question = QuestionFactory.create(letter=letter)
        response = ResponseFactory.create(
            question=question, participant=member, response_text="member text"
        )
        db_session.commit()

        rv = authenticated_client.post(
            f"/responses/response/{response.api_identifier}:edit_response",
            json={"response_text": "admin fix"},
        )

        assert rv.status_code == 200
        assert rv.json()["response_text"] == "admin fix"
        db_session.refresh(response)
        assert response.response_text == "admin fix"
        assert response.participant == member

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
            "Cannot write a response as a different participant"
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

    @pytest.mark.parametrize("participant_id", ["self", "omit", "null"])
    def test_upsert_creates_then_updates_caller_response(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
        participant_id: str,
    ) -> None:
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin, current_user])
        letter = LetterFactory.create(
            group=group, status=LetterStatus.IN_PROGRESS
        )
        question = QuestionFactory.create(letter=letter)
        db_session.commit()

        def body(text: str) -> dict[str, str | None]:
            payload: dict[str, str | None] = {"response_text": text}
            if participant_id == "self":
                payload["participant_api_identifier"] = (
                    current_user.api_identifier
                )
            elif participant_id == "null":
                payload["participant_api_identifier"] = None
            return payload

        created = authenticated_client.post(
            f"/questions/question/{question.api_identifier}:upsert_response",
            json=body("first"),
        )
        assert created.status_code == 200
        db_session.refresh(question)
        mine = [
            resp
            for resp in question.responses
            if resp.participant_id == current_user.id
        ]
        assert len(mine) == 1
        assert mine[0].response_text == "first"

        updated = authenticated_client.post(
            f"/questions/question/{question.api_identifier}:upsert_response",
            json=body("second"),
        )
        assert updated.status_code == 200
        db_session.refresh(mine[0])
        db_session.refresh(question)
        assert mine[0].response_text == "second"
        assert mine[0].participant_id == current_user.id
        assert len(question.responses) == 1

    def test_upsert_by_own_response_id_updates(
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
            question=question, participant=current_user, response_text="draft"
        )
        db_session.commit()

        rv = authenticated_client.post(
            f"/questions/question/{question.api_identifier}:upsert_response",
            json={
                "response_text": "updated",
                "api_identifier": response.api_identifier,
            },
        )

        assert rv.status_code == 200
        db_session.refresh(response)
        assert response.response_text == "updated"
        assert response.participant_id == current_user.id

    @pytest.mark.parametrize(
        "case",
        [
            "admin_other_participant",
            "member_other_response",
            "admin_other_response",
        ],
    )
    def test_upsert_rejects_writing_as_someone_else(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
        case: str,
    ) -> None:
        owner = UserFactory.create()
        if case == "member_other_response":
            admin = UserFactory.create()
            group = GroupFactory.create(
                admin=admin, members=[admin, owner, current_user]
            )
        else:
            group = GroupFactory.create(
                admin=current_user, members=[current_user, owner]
            )
        letter = LetterFactory.create(
            group=group, status=LetterStatus.IN_PROGRESS
        )
        question = QuestionFactory.create(letter=letter)
        response = ResponseFactory.create(
            question=question, participant=owner, response_text="owner text"
        )
        db_session.commit()

        body = {"response_text": "hijacked"}
        if case == "admin_other_participant":
            body["participant_api_identifier"] = owner.api_identifier
        else:
            body["api_identifier"] = response.api_identifier

        rv = authenticated_client.post(
            f"/questions/question/{question.api_identifier}:upsert_response",
            json=body,
        )

        assert rv.status_code == 403
        assert rv.json()["detail"] == (
            "Cannot write a response as a different participant"
        )
        db_session.refresh(response)
        assert response.response_text == "owner text"

    def test_upsert_rejects_response_from_another_question(
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
        other_question = QuestionFactory.create(letter=letter)
        other_response = ResponseFactory.create(
            question=other_question,
            participant=current_user,
            response_text="elsewhere",
        )
        db_session.commit()

        rv = authenticated_client.post(
            f"/questions/question/{question.api_identifier}:upsert_response",
            json={
                "response_text": "moved",
                "api_identifier": other_response.api_identifier,
            },
        )

        assert rv.status_code == 400
        assert rv.json()["detail"] == (
            "Response does not belong to this question"
        )
        db_session.refresh(other_response)
        db_session.refresh(question)
        assert other_response.response_text == "elsewhere"
        assert other_response.question_id == other_question.id
        assert question.responses == []

    def test_non_owner_response_on_another_question_is_forbidden(
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
        other_question = QuestionFactory.create(letter=letter)
        other_response = ResponseFactory.create(
            question=other_question,
            participant=owner,
            response_text="owner text",
        )
        db_session.commit()

        rv = authenticated_client.post(
            f"/questions/question/{question.api_identifier}:upsert_response",
            json={
                "response_text": "hijacked",
                "api_identifier": other_response.api_identifier,
            },
        )

        assert rv.status_code == 403
        assert rv.json()["detail"] == (
            "Cannot write a response as a different participant"
        )
        db_session.refresh(other_response)
        assert other_response.response_text == "owner text"

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

    @pytest.mark.parametrize(
        "letter_type", [LetterType.CYCLIC, LetterType.ADHOC]
    )
    def test_other_member_cannot_delete_in_progress_question(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
        letter_type: LetterType,
    ) -> None:
        """Membership is not enough: only the author or admin may delete."""
        author = UserFactory.create()
        admin = UserFactory.create()
        group = GroupFactory.create(
            admin=admin, members=[admin, author, current_user]
        )
        question = QuestionFactory.create(
            author=author,
            letter=LetterFactory.create(
                group=group,
                status=LetterStatus.IN_PROGRESS,
                letter_type=letter_type,
            ),
        )
        db_session.commit()

        rv = authenticated_client.delete(
            f"/questions/question/{question.api_identifier}"
        )

        assert rv.status_code == 403
        assert rv.json()["detail"] == (
            "Only the question author or group admin can delete a question"
        )
        db_session.refresh(question)
        assert question.id is not None
