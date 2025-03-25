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

    :param db: Database session
    :param letter_api_id: API identifier of the letter
    :param skip: Number of records to skip, defaults to 0
    :param limit: Maximum number of records to return, defaults to 100
    :return: Sequence of questions
    :rtype: Sequence[Question]
    :raises IDNotFoundException: If letter with given API ID is not found
    """
    letter = api_identifier_crud.get_model(db, Letter, api_id=letter_api_id)
    return db.scalars(
        select(Question)
        .filter(Question.letter == letter)
        .offset(skip)
        .limit(
            limit,
        )
    ).all()


def _validate_response(
    question: Question,
    user: User,
) -> None:
    """Validate that a user can respond to a question.

    :param question: Question to validate response for
    :param user: User attempting to respond
    :raises ValueError: If user is not a participant or has already responded
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

    :param db: Database session
    :param question: Question to respond to
    :param user: User creating the response
    :param response_text: Text content of the response
    :return: Newly created response
    :rtype: Response
    :raises ValueError: If user is not a participant or has already responded
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

    :param db: Database session
    :param response: Response to update
    :param response_text: New text content for the response
    :return: Updated response
    :rtype: Response
    """
    response.response_text = response_text
    db.add(response)
    return response
