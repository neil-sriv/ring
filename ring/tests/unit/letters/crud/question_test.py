"""Tests for question CRUD operations.

This module contains tests for all question-related CRUD operations,
including deletion and validation of deletion rules.
"""

import pytest
from sqlalchemy.orm import Session

from ring.letters.crud import question as question_crud
from ring.letters.models.question_model import Question
from ring.letters.models.response_model import Response
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.letters.response_factory import ResponseFactory


class TestQuestionCrud:
    """Test suite for question CRUD operations."""

    def test_delete_question_without_responses(
        self, db_session: Session
    ) -> None:
        """Test deleting a question that has no responses.

        This test verifies that:
        1. A question without responses can be deleted
        2. The question is removed from the database
        3. The deletion is successful

        Args:
            db_session (Session): Database session
        """
        question = QuestionFactory.create()
        db_session.commit()

        question_crud.delete_question(db_session, question)
        db_session.commit()

        # Verify question is deleted
        assert (
            db_session.query(Question).filter_by(id=question.id).one_or_none()
            is None
        )

    def test_delete_question_with_responses(self, db_session: Session) -> None:
        """Test attempting to delete a question that has responses.

        This test verifies that:
        1. A question with responses cannot be deleted
        2. The appropriate error is raised
        3. The question and its responses remain in the database

        Args:
            db_session (Session): Database session
        """
        question = QuestionFactory.create()
        response = ResponseFactory.create(question=question)
        db_session.commit()

        # Attempt to delete should raise ValueError
        with pytest.raises(
            ValueError, match="Cannot delete a question that has responses"
        ):
            question_crud.delete_question(db_session, question)

        # Verify question and response still exist
        db_session.refresh(question)
        assert db_session.query(Question).filter_by(id=question.id).one()
        assert db_session.query(Response).filter_by(id=response.id).one()
