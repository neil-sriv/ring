"""Tests for question API endpoints.

This module contains tests for all question-related API endpoints,
including deletion and authorization checks.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.letters.constants import LetterStatus, LetterType
from ring.letters.models.question_model import Question
from ring.letters.models.response_model import Response
from ring.parties.models.user_model import User
from ring.tests.factories.letters.letter_factory import (
    LetterFactory,
    UpcomingLetterFactory,
)
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.letters.response_factory import ResponseFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory


class TestQuestionAPI:
    """Test suite for question API endpoints."""

    def test_delete_question_as_author(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        """Test deleting a question as the author.

        This test verifies that:
        1. The author can delete their own question
        2. The deletion is successful
        3. The response is correct

        Args:
            authenticated_client (TestClient): FastAPI test client
            db_session (Session): Database session
        """
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin, current_user])
        letter = UpcomingLetterFactory.create(group=group)
        question = QuestionFactory.create(author=current_user, letter=letter)
        db_session.commit()

        response = authenticated_client.delete(
            f"/questions/question/{question.api_identifier}"
        )
        assert response.status_code == 204

        # Verify question is deleted
        assert (
            db_session.query(Question).filter_by(id=question.id).one_or_none()
            is None
        )

    def test_delete_question_as_group_admin(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        """Test deleting a question as the group admin.

        This test verifies that:
        1. The group admin can delete any question in their group
        2. The deletion is successful
        3. The response is correct

        Args:
            authenticated_client (TestClient): FastAPI test client
            db_session (Session): Database session
        """
        group = GroupFactory.create(admin=current_user)
        letter = UpcomingLetterFactory.create(group=group)
        question = QuestionFactory.create(letter=letter)
        db_session.commit()

        response = authenticated_client.delete(
            f"/questions/question/{question.api_identifier}"
        )
        assert response.status_code == 204

        # Verify question is deleted
        assert (
            db_session.query(Question).filter_by(id=question.id).one_or_none()
            is None
        )

    def test_delete_question_unauthorized(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        """Test attempting to delete a question without proper authorization.

        This test verifies that:
        1. A non-author, non-admin group member cannot delete a question
        2. The appropriate error response is returned
        3. The question remains in the database

        Args:
            authenticated_client (TestClient): FastAPI test client
            db_session (Session): Database session
        """
        author = UserFactory.create()
        admin = UserFactory.create()
        group = GroupFactory.create(
            admin=admin, members=[admin, author, current_user]
        )
        letter = UpcomingLetterFactory.create(group=group)
        question = QuestionFactory.create(author=author, letter=letter)
        db_session.commit()

        response = authenticated_client.delete(
            f"/questions/question/{question.api_identifier}"
        )
        assert response.status_code == 403
        assert (
            response.json()["detail"]
            == "Only the question author or group admin can delete a question"
        )

        # Verify question still exists
        assert db_session.query(Question).filter_by(id=question.id).one()

    def test_delete_question_non_member(
        self, authenticated_client: TestClient, db_session: Session
    ) -> None:
        """Non-members get the Casbin membership denial, not the author/admin
        message, so missing membership cannot be used to probe question ids.
        """
        author = UserFactory.create()
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin)
        letter = UpcomingLetterFactory.create(group=group)
        question = QuestionFactory.create(author=author, letter=letter)
        db_session.commit()

        response = authenticated_client.delete(
            f"/questions/question/{question.api_identifier}"
        )
        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Not authorized to access this resource"
        )

        assert db_session.query(Question).filter_by(id=question.id).one()

    def test_delete_question_with_responses(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        """Test attempting to delete a question that has responses.

        This test verifies that:
        1. A question with responses cannot be deleted, even by authorized users
        2. The appropriate error response is returned
        3. The question and its responses remain in the database

        Args:
            authenticated_client (TestClient): FastAPI test client
            db_session (Session): Database session
        """
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin, current_user])
        letter = UpcomingLetterFactory.create(group=group)
        question = QuestionFactory.create(
            author=current_user,
            letter=letter,
        )
        response = ResponseFactory.create(question=question)
        db_session.commit()

        rv = authenticated_client.delete(
            f"/questions/question/{question.api_identifier}"
        )
        assert rv.status_code == 400
        assert (
            rv.json()["detail"]
            == "Cannot delete a question that has responses"
        )

        # Verify question and response still exist
        assert db_session.query(Question).filter_by(id=question.id).one()
        assert db_session.query(Response).filter_by(id=response.id).one()

    def test_delete_nonexistent_question(
        self, authenticated_client: TestClient, db_session: Session
    ) -> None:
        """Missing question ids map to 403 (anti-enumeration via load_and_check).

        Args:
            authenticated_client (TestClient): FastAPI test client
            db_session (Session): Database session
        """
        response = authenticated_client.delete(
            "/questions/question/qstn_nonexistent"
        )
        assert response.status_code == 403
        assert response.json()["detail"] == (
            "Not authorized to access this resource"
        )

    @pytest.mark.parametrize(
        "letter_type", [LetterType.CYCLIC, LetterType.ADHOC]
    )
    def test_author_deletes_unanswered_question_on_in_progress(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
        letter_type: LetterType,
    ) -> None:
        """The author can delete an unanswered question on an in-progress loop."""
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin, current_user])
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            letter_type=letter_type,
        )
        question = QuestionFactory.create(author=current_user, letter=letter)
        db_session.commit()

        response = authenticated_client.delete(
            f"/questions/question/{question.api_identifier}"
        )
        assert response.status_code == 204
        assert (
            db_session.query(Question).filter_by(id=question.id).one_or_none()
            is None
        )

    @pytest.mark.parametrize(
        "letter_type", [LetterType.CYCLIC, LetterType.ADHOC]
    )
    def test_admin_deletes_unanswered_question_on_in_progress(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
        letter_type: LetterType,
    ) -> None:
        """A group admin can delete another member's unanswered in-progress question."""
        author = UserFactory.create()
        group = GroupFactory.create(
            admin=current_user, members=[current_user, author]
        )
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            letter_type=letter_type,
        )
        question = QuestionFactory.create(author=author, letter=letter)
        db_session.commit()

        response = authenticated_client.delete(
            f"/questions/question/{question.api_identifier}"
        )
        assert response.status_code == 204
        assert (
            db_session.query(Question).filter_by(id=question.id).one_or_none()
            is None
        )

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
        """Another member cannot delete an in-progress question."""
        author = UserFactory.create()
        admin = UserFactory.create()
        group = GroupFactory.create(
            admin=admin, members=[admin, author, current_user]
        )
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            letter_type=letter_type,
        )
        question = QuestionFactory.create(author=author, letter=letter)
        db_session.commit()

        response = authenticated_client.delete(
            f"/questions/question/{question.api_identifier}"
        )
        assert response.status_code == 403
        assert (
            response.json()["detail"]
            == "Only the question author or group admin can delete a question"
        )
        assert db_session.query(Question).filter_by(id=question.id).one()

    @pytest.mark.parametrize(
        "letter_type", [LetterType.CYCLIC, LetterType.ADHOC]
    )
    def test_cannot_delete_answered_question_on_in_progress(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
        letter_type: LetterType,
    ) -> None:
        """An in-progress question that already has an answer cannot be deleted."""
        admin = UserFactory.create()
        group = GroupFactory.create(admin=admin, members=[admin, current_user])
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            letter_type=letter_type,
        )
        question = QuestionFactory.create(author=current_user, letter=letter)
        answer = ResponseFactory.create(question=question)
        db_session.commit()

        response = authenticated_client.delete(
            f"/questions/question/{question.api_identifier}"
        )
        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == "Cannot delete a question that has responses"
        )
        assert db_session.query(Question).filter_by(id=question.id).one()
        assert db_session.query(Response).filter_by(id=answer.id).one()

    @pytest.mark.parametrize(
        "letter_type", [LetterType.CYCLIC, LetterType.ADHOC]
    )
    def test_cannot_delete_question_from_sent_loop(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
        letter_type: LetterType,
    ) -> None:
        """A sent loop rejects deletion even when the question has no answers."""
        group = GroupFactory.create(admin=current_user)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.SENT,
            letter_type=letter_type,
        )
        question = QuestionFactory.create(author=current_user, letter=letter)
        db_session.commit()

        response = authenticated_client.delete(
            f"/questions/question/{question.api_identifier}"
        )
        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == "Cannot delete a question from a loop that has been sent"
        )
        assert db_session.query(Question).filter_by(id=question.id).one()
