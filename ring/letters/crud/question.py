"""CRUD operations for question management.

This module provides functions for managing questions and responses in letters,
including validation of user responses and response editing.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Sequence

from llm_service import ApiClient, CompletionRequest, CompletionsApi
from loguru import logger
from pydantic import BaseModel
from sqlalchemy import select

from ring.api_identifier import util as api_identifier_crud
from ring.fastapp.config import get_llm_config
from ring.letters.crud.response import create_response
from ring.letters.models.letter_model import Letter
from ring.letters.models.question_model import Question
from ring.letters.models.response_model import Response
from ring.parties.models.user_model import User
from ring.search.crud.hybrid_search import (
    create_hybrid_search_document,
    register_search_function,
)
from ring.search.models.hybrid_search import (
    HybridSearchDocument,
    SearchableType,
)

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
    return create_response(db, question, user, response_text)


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


def delete_question(
    db: Session,
    question: Question,
) -> None:
    """Delete a question.

    Args:
        db (Session): Database session
        question (Question): Question to delete

    Raises:
        ValueError: If the question has responses and cannot be deleted
    """
    if question.responses:
        raise ValueError("Cannot delete a question that has responses")

    # Delete the question
    db.delete(question)


def generate_question(prompt: str, letter: Letter | None = None) -> str:
    """
    Generate a question using LLM service.

    :param prompt: Prompt to generate the question
    :return: Generated question text
    """
    # Initialize LLM service
    api_client = ApiClient(configuration=get_llm_config().config)
    api_instance = CompletionsApi(api_client=api_client)

    def _compile_existing_questions(letter: Letter) -> str:
        logger.warning(f"Letter: {letter}")
        return "\n".join([q.question_text for q in letter.questions])

    # generate system prompt
    system_prompt = f"""
    You are a helpful assistant that generates questions for a private newsletter service used by a group of friends. 
    The newsletter is sent to the group on a regular basis, and the questions are used to generate the newsletter.
    The questions should be short and to the point, and should be easy and fun to answer.

    """

    if letter is not None:
        system_prompt += f"""
        These are the existing questions for this letter:
        {_compile_existing_questions(letter)}
        """

    if prompt is not None:
        additional_instructions = f"""
        You have been given a prompt that will be used to generate the question from the user.
        {prompt}
        """
        system_prompt += additional_instructions

    class OutputFormat(BaseModel):
        question_text: str
        # extra_information: Optional[str]

    # Generate question using LLM
    completion_request = CompletionRequest(
        prompt=system_prompt,
        output_schema_definition=json.dumps(OutputFormat.model_json_schema()),
    )
    logger.info(f"Completion Request: {completion_request}")
    response = api_instance.generate_completion_completions_generate_post(
        completion_request
    )
    logger.info(f"LLM Response: {response}")
    output = OutputFormat.model_validate_json(response.output_schema)

    return output.question_text


def create_question(
    db: Session, letter: Letter, question_text: str, author: User | None = None
) -> Question:
    """Create a question.

    Args:
        db (Session): Database session
        letter (Letter): Letter to add question to
        question_text (str): Text of the question
        author (User | None, optional): Author of the question. Defaults to None.

    Returns:
        Question: Created question
    """
    db_question = Question.create(letter, question_text, author=author)
    db.add(db_question)
    if search_document := create_question_search_document(db, db_question):
        db.add(search_document)
    return db_question


@register_search_function(SearchableType.QUESTION, Question)
def create_question_search_document(
    db: Session, question: Question
) -> HybridSearchDocument:
    """Create a search document for a question.

    Args:
        db (Session): Database session
        question (Question): Question to create a search document for

    Returns:
        HybridSearchDocument: Search document for the question
    """
    author_name = question.author.name if question.author else ""
    raw_text = f"{question.question_text} {author_name}"
    return create_hybrid_search_document(
        db, raw_text, question.api_identifier, SearchableType.QUESTION
    )
