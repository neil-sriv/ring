from __future__ import annotations

import itertools
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Sequence

from fastapi import APIRouter, Depends
from sqlalchemy import ColumnElement, and_, or_

from ring.api_identifier import (
    util as api_identifier_crud,
)
from ring.dependencies import (
    AuthenticatedRequestDependencies,
    get_request_dependencies,
)
from ring.letters.constants import LetterStatus
from ring.letters.crud import letter as letter_crud
from ring.letters.crud import response as response_crud
from ring.letters.models.letter_model import Letter
from ring.letters.schemas.letter import LetterCreate, LetterUpdate
from ring.letters.schemas.question import QuestionCreate
from ring.letters.schemas.response import ResponseUnlinked
from ring.parties.models.user_model import User
from ring.ring_pydantic import PublicLetter as LetterSchema
from ring.ring_pydantic.linked_schemas import DashboardLetters

router = APIRouter()


@router.post("/letter", response_model=LetterSchema)
async def add_next_letter(
    letter: LetterCreate,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Letter:
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


@router.get("/letters/", response_model=Sequence[LetterSchema])
async def list_letters(
    group_api_id: str,
    skip: int = 0,
    limit: int = 100,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Sequence[Letter]:
    letters = letter_crud.get_letters(
        req_dep.db, group_api_id=group_api_id, skip=skip, limit=limit
    )
    return letters


@router.get("/letter/{letter_api_id}", response_model=LetterSchema)
async def read_letter(
    letter_api_id: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Letter:
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
) -> dict[str, list[Letter]]:
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
    return {
        "upcoming": grouped_letters.get(LetterStatus.UPCOMING, []),
        "in_progress": grouped_letters.get(LetterStatus.IN_PROGRESS, []),
        "recently_completed": grouped_letters.get(LetterStatus.SENT, []),
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
    db_letter = api_identifier_crud.get_model(
        req_dep.db,
        Letter,
        api_id=letter_api_id,
    )
    curr_time = datetime.now(tz=UTC)
    if db_letter.status == LetterStatus.UPCOMING:
        assert (
            letter.send_at > db_letter.group.in_progress_letter.send_at
            if db_letter.group.in_progress_letter
            else letter.send_at > curr_time
        )
    else:
        assert letter.send_at > curr_time
    letter_crud.edit_letter(req_dep.db, db_letter, letter.send_at)
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


@router.patch(
    "/letter/{letter_api_id}:bulk_edit_responses",
    response_model=LetterSchema,
    deprecated=True,
)
async def bulk_edit_responses(
    letter_api_id: str,
    updated_responses: Sequence[ResponseUnlinked],
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Letter:
    db_letter = api_identifier_crud.get_model(
        req_dep.db,
        Letter,
        api_id=letter_api_id,
    )
    db_responses = response_crud.get_responses(
        req_dep.db,
        db_letter,
        [resp.api_identifier for resp in updated_responses],
    )
    response_map = {resp.api_identifier: resp for resp in db_responses}
    response_crud.edit_responses(response_map, updated_responses)
    req_dep.db.commit()
    req_dep.db.refresh(db_letter)
    return db_letter
