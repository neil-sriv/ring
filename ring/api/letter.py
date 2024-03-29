from __future__ import annotations
from fastapi import Depends
from ring.dependencies import (
    AuthenticatedRequestDependencies,
    get_request_dependencies,
)
from typing import Sequence
from ring.crud import (
    letter as letter_crud,
    api_identifier as api_identifier_crud,
)
from ring.pydantic_schemas import LetterLinked as LetterSchema
from ring.pydantic_schemas.letter import LetterCreate
from ring.postgres_models.letter_model import Letter
from ring.pydantic_schemas.question import QuestionCreate
from ring.routes import internal


@internal.post("/letter", response_model=LetterSchema)
async def add_next_letter(
    letter: LetterCreate,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Letter:
    db_letter = letter_crud.create_letter(
        db=req_dep.db,
        group_api_id=letter.group_api_identifier,
    )
    req_dep.db.commit()
    return db_letter


@internal.get("/letters/", response_model=Sequence[LetterSchema])
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


@internal.get("/letter/{letter_api_id}", response_model=LetterSchema)
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


@internal.post(
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
    letter_crud.add_question(req_dep.db, db_letter, question.question_text)
    req_dep.db.refresh(db_letter)
    req_dep.db.commit()
    return db_letter
