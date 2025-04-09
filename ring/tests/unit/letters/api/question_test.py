"""Tests for question API endpoints.

This module contains tests for all question-related API endpoints,
including deletion and authorization checks.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.letters.models.question_model import Question
from ring.letters.models.response_model import Response
from ring.parties.models.user_model import User
from ring.tests.factories.letters.letter_factory import UpcomingLetterFactory
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
        question = QuestionFactory.create(
            author=current_user, letter=UpcomingLetterFactory.create()
        )
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
        self, authenticated_client: TestClient, db_session: Session
    ) -> None:
        """Test attempting to delete a question without proper authorization.

        This test verifies that:
        1. A non-author, non-admin user cannot delete a question
        2. The appropriate error response is returned
        3. The question remains in the database

        Args:
            authenticated_client (TestClient): FastAPI test client
            db_session (Session): Database session
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
        assert (
            response.json()["detail"]
            == "Only the question author or group admin can delete a question"
        )

        # Verify question still exists
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
        question = QuestionFactory.create(
            author=current_user,
            letter=UpcomingLetterFactory.create(),
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
        """Test attempting to delete a nonexistent question.

        This test verifies that:
        1. Attempting to delete a nonexistent question returns 404
        2. The appropriate error response is returned

        Args:
            authenticated_client (TestClient): FastAPI test client
            db_session (Session): Database session
        """
        response = authenticated_client.delete(
            "/questions/question/qstn_nonexistent"
        )
        assert response.status_code == 404

    def test_delete_question_from_in_progress_loop(
        self,
        authenticated_client: TestClient,
        current_user: User,
        db_session: Session,
    ) -> None:
        """Test deleting a question from a loop that is in progress.

        This test verifies that:
        1. A question cannot be deleted if its loop is not UPCOMING
        2. The appropriate error response (400) is returned
        3. The question remains in the database

        Args:
            authenticated_client (TestClient): FastAPI test client
            current_user (User): The authenticated user
            db_session (Session): Database session
        """
        question = QuestionFactory.create(author=current_user)
        db_session.commit()

        response = authenticated_client.delete(
            f"/questions/question/{question.api_identifier}"
        )
        assert response.status_code == 400
        assert (
            response.json()["detail"]
            == "Cannot delete a question from a loop that is in progress"
        )

        # Verify question still exists
        assert db_session.query(Question).filter_by(id=question.id).one()
