"""CRUD operations for question management.

This module provides functions for managing questions and responses in letters,
including validation of user responses and response editing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from sqlalchemy import select

from ring.api_identifier import util as api_identifier_crud
from ring.letters.models.letter_model import Letter
from ring.letters.models.question_model import Question
from ring.letters.models.response_model import Response
from ring.parties.models.user_model import User

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_questions(
    db: Session, letter_api_id: str, skip: int = 0, limit: int = 100
) -> Sequence[Question]:
    """Retrieve questions for a specific letter with pagination.

    Args:
        db (Session): Database session
        letter_api_id (str): API identifier of the letter
        skip (int, optional): Number of records to skip. Defaults to 0.
        limit (int, optional): Maximum number of records to return. Defaults to 100.

    Returns:
        Sequence[Question]: List of questions

    Raises:
        IDNotFoundException: If letter with given API ID is not found
    """
    letter = api_identifier_crud.get_model(db, Letter, api_id=letter_api_id)
    return db.scalars(
        select(Question)
        .filter(Question.letter == letter)
        .offset(skip)
        .limit(limit)
    ).all()


def _validate_response(
    question: Question,
    user: User,
) -> None:
    """Validate that a user can respond to a question.

    Args:
        question (Question): Question to validate response for
        user (User): User attempting to respond

    Raises:
        ValueError: If user is not a participant or has already responded
    """
    if user not in question.letter.participants:
        raise ValueError("User is not a participant in the letter.")
    if user.id in [resp.participant_id for resp in question.responses]:
        raise ValueError("User has already responded to this question.")


def add_response(
    db: Session,
    question: Question,
    user: User,
    response_text: str,
) -> Response:
    """Add a new response to a question.

    Args:
        db (Session): Database session
        question (Question): Question to respond to
        user (User): User creating the response
        response_text (str): Text content of the response

    Returns:
        Response: Newly created response

    Raises:
        ValueError: If user is not a participant or has already responded
    """
    _validate_response(question, user)
    response = Response.create(user, question, response_text)
    db.add(response)
    question.responses.append(response)
    return response


def edit_response(
    db: Session,
    response: Response,
    response_text: str,
) -> Response:
    """Update the text content of a response.

    Args:
        db (Session): Database session
        response (Response): Response to update
        response_text (str): New text content for the response

    Returns:
        Response: Updated response
    """
    response.response_text = response_text
    db.add(response)
    return response
