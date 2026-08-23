"""Letter API endpoints.

This module provides FastAPI endpoints for managing letters, including creation,
retrieval, updates, and dashboard views. It handles letter scheduling, question
management, and user access control.
"""

from __future__ import annotations

import itertools
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any, Sequence

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy import ColumnElement, and_, or_

from ring.api_identifier import (
    util as api_identifier_crud,
)
from ring.authz.authz import bulk_load_and_check, load_and_check
from ring.authz.enforcer import Action
from ring.fastapp.dependencies import (
    AuthenticatedRequestDependencies,
    get_request_dependencies,
)
from ring.letters.constants import LetterStatus, LetterType
from ring.letters.crud import letter as letter_crud
from ring.letters.crud import question as question_crud
from ring.letters.models.letter_model import Letter
from ring.letters.schemas.letter import LetterCreate, LetterUpdate
from ring.letters.schemas.question import (
    GenerateQuestionRequest,
    GenerateQuestionResponse,
    QuestionCreate,
)
from ring.parties.models.user_model import User
from ring.ring_pydantic import PublicLetter as LetterSchema
from ring.ring_pydantic.linked_schemas import DashboardLetters, MinimalLetter

router = APIRouter()


@router.post("/letter", response_model=LetterSchema)
async def add_next_letter(
    letter: LetterCreate,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Letter:
    """Create a new letter for a group.

    Creates a new letter with default questions if there are no letters
    currently in progress or upcoming for the group.

    Args:
        letter (LetterCreate): Letter creation parameters
        req_dep (AuthenticatedRequestDependencies): Request dependencies including database session and auth

    Returns:
        Letter: Newly created letter

    Raises:
        ValueError: If there is already a letter in progress or upcoming
    """
    group_letters = letter_crud.get_letters(
        req_dep.db, group_api_id=letter.group_api_identifier
    )
    if any(
        letter.status in [LetterStatus.IN_PROGRESS, LetterStatus.UPCOMING]
        for letter in group_letters
    ):
        raise ValueError(
            "There is already a letter in progress or upcoming for this group"
        )
    db_letter = letter_crud.create_letter_with_questions(
        req_dep.db,
        group_api_id=letter.group_api_identifier,
        send_at=letter.send_at,
        letter_status=LetterStatus.UPCOMING,
    )
    req_dep.db.commit()
    return db_letter


@router.post("/letter:{letter_type}", response_model=LetterSchema)
async def add_next_letter(
    letter_type: LetterType,
    letter: LetterCreate,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Letter:
    db_group = load_and_check(
        req_dep.db,
        req_dep.current_user,
        Action.READ,
        letter.group_api_identifier,
    )
    db_letter = letter_crud.create_letter(
        req_dep.db,
        group_api_id=db_group.api_identifier,
        send_at=letter.send_at,
        letter_status=LetterStatus.UPCOMING,
        letter_type=letter_type,
        title=letter.title,
    )
    req_dep.db.commit()
    return db_letter


@router.get("/letters/", response_model=Sequence[MinimalLetter])
async def list_letters(
    group_api_id: str,
    letter_type: LetterType | None = None,
    skip: int = 0,
    limit: int = 100,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Sequence[Letter]:
    """List letters for a specific group.

    Retrieves a paginated list of letters belonging to the specified group.

    Args:
        group_api_id (str): API identifier of the group
        skip (int, optional): Number of records to skip for pagination. Defaults to 0.
        limit (int, optional): Maximum number of records to return. Defaults to 100.
        req_dep (AuthenticatedRequestDependencies): Request dependencies including database session and auth

    Returns:
        Sequence[Letter]: List of letters
    """
    letters = letter_crud.get_letters(
        req_dep.db,
        group_api_id=group_api_id,
        letter_type=letter_type,
        skip=skip,
        limit=limit,
    )
    return letters


@router.get("/letter/{letter_api_id}", response_model=LetterSchema)
async def read_letter(
    letter_api_id: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Letter:
    """Retrieve a specific letter by its API identifier.

    Args:
        letter_api_id (str): API identifier of the letter
        req_dep (AuthenticatedRequestDependencies): Request dependencies including database session and auth

    Returns:
        Letter: The requested letter

    Raises:
        IDNotFoundException: If letter with given API ID is not found
    """
    db_letter = api_identifier_crud.get_model(
        req_dep.db,
        Letter,
        api_id=letter_api_id,
    )
    return db_letter


@router.get("/letters:dashboard", response_model=DashboardLetters)
async def list_dashboard_letters(
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> dict[str, Any]:
    """List letters for the dashboard view.

    Retrieves letters that are upcoming, in progress, or recently completed
    (within the last 8 days) for the current user. In-progress letters come
    with a per-letter map of the questions the current user has not answered
    yet, so the dashboard can build "waiting on you" cards without the full
    question/response payload.

    Args:
        req_dep (AuthenticatedRequestDependencies): Request dependencies including database session and auth

    Returns:
        dict[str, Any]: Dictionary containing categorized letters and the
            current user's unanswered questions per in-progress letter
    """
    time = datetime.now(tz=UTC) - timedelta(days=8)
    filters: list[ColumnElement[bool]] = [
        or_(
            Letter.status.in_(
                [LetterStatus.UPCOMING, LetterStatus.IN_PROGRESS]
            ),
            and_(
                Letter.status == LetterStatus.SENT,
                Letter.send_at > time,
            ),
        )
    ]
    letters = letter_crud.get_letters_for_user(
        req_dep.db, req_dep.current_user, filters=filters
    )
    grouped_letters: dict[str, list[Letter]] = defaultdict(list)
    for k, g in itertools.groupby(letters, key=lambda letter: letter.status):
        grouped_letters[k].extend(g)
    in_progress_letters = grouped_letters.get(LetterStatus.IN_PROGRESS, [])
    unanswered_questions = {
        letter.api_identifier: question_crud.unanswered_questions_for_user(
            letter, req_dep.current_user
        )
        for letter in in_progress_letters
    }
    return {
        "upcoming": grouped_letters.get(LetterStatus.UPCOMING, []),
        "in_progress": in_progress_letters,
        "recently_completed": grouped_letters.get(LetterStatus.SENT, []),
        "unanswered_questions": unanswered_questions,
    }


@router.post(
    "/letter/{letter_api_id}:edit_letter",
    response_model=LetterSchema,
)
async def edit_letter(
    letter_api_id: str,
    letter: LetterUpdate,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Letter:
    """Update a letter's details.

    Updates the send time of a letter. For upcoming letters, ensures the new
    send time is after any in-progress letter's send time.

    Args:
        letter_api_id (str): API identifier of the letter to edit
        letter (LetterUpdate): Updated letter details
        req_dep (AuthenticatedRequestDependencies): Request dependencies including database session and auth

    Returns:
        Letter: Updated letter

    Raises:
        AssertionError: If new send time violates timing constraints
        IDNotFoundException: If letter with given API ID is not found
    """
    db_letter = api_identifier_crud.get_model(
        req_dep.db,
        Letter,
        api_id=letter_api_id,
    )
    if db_letter.status == LetterStatus.SENT:
        raise HTTPException(
            status_code=400,
            detail="Cannot edit a sent letter",
        )
    if letter.send_at:
        curr_time = datetime.now(tz=UTC)
        if db_letter.status == LetterStatus.UPCOMING:
            assert (
                letter.send_at > db_letter.group.in_progress_letters[0].send_at
                if db_letter.group.in_progress_letters
                else letter.send_at > curr_time
            )
        else:
            assert letter.send_at > curr_time

    letter_crud.edit_letter(
        req_dep.db,
        db_letter,
        send_at=letter.send_at,
        title=letter.title,
        status=letter.status,
    )
    req_dep.db.commit()
    return db_letter


@router.post(
    "/letter/{letter_api_id}:add_question",
    response_model=LetterSchema,
)
async def add_question(
    letter_api_id: str,
    question: QuestionCreate,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Letter:
    """Add a new question to a letter.

    Creates and adds a new question to the specified letter. The question can
    optionally be associated with an author.

    :param letter_api_id: API identifier of the letter
    :type letter_api_id: str
    :param question: Question creation parameters
    :type question: QuestionCreate
    :param req_dep: Request dependencies including database session and auth
    :type req_dep: AuthenticatedRequestDependencies
    :raises IDNotFoundException: If letter or author with given API ID is not found
    :return: Updated letter with the new question
    :rtype: Letter
    """
    db_letter = api_identifier_crud.get_model(
        req_dep.db,
        Letter,
        api_id=letter_api_id,
    )
    db_author = (
        api_identifier_crud.get_model(
            req_dep.db,
            User,
            api_id=question.author_api_id,
        )
        if question.author_api_id
        else None
    )
    letter_crud.add_question(
        req_dep.db, db_letter, question.question_text, author=db_author
    )
    req_dep.db.refresh(db_letter)
    req_dep.db.commit()
    return db_letter


@router.post(
    "/letter/{letter_api_id}:generate_question",
    response_model=GenerateQuestionResponse,
)
async def generate_question(
    letter_api_id: str,
    request: GenerateQuestionRequest,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> GenerateQuestionResponse:
    """Generate a question using LLM without saving it."""
    db_letter = api_identifier_crud.get_model(
        req_dep.db, Letter, api_id=letter_api_id
    )
    generated_text = question_crud.generate_question(request.prompt, db_letter)
    return GenerateQuestionResponse(generated_text=generated_text)
