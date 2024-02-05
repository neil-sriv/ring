from __future__ import annotations
from fastapi import Depends
from ring.dependencies import get_db
from typing import TYPE_CHECKING, Sequence
from ring.crud import letter as letter_crud, api_identifier as api_identifier_crud
from ring.pydantic_schemas import LetterLinked as LetterSchema
from ring.pydantic_schemas.letter import LetterCreate
from ring.postgres_models.letter_model import Letter
from ring.pydantic_schemas.question import QuestionCreate
from ring.routes import internal

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@internal.post("/letter", response_model=LetterSchema)
async def add_next_letter(
    letter: LetterCreate,
    db: Session = Depends(get_db),
) -> Letter:
    db_letter = letter_crud.create_letter(
        db=db,
        group_api_id=letter.group_api_identifier,
    )
    db.commit()
    return db_letter


@internal.get("/letters/", response_model=Sequence[LetterSchema])
async def list_letters(
    group_api_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> Sequence[Letter]:
    letters = letter_crud.get_letters(
        db, group_api_id=group_api_id, skip=skip, limit=limit
    )
    return letters


@internal.get("/letter/{letter_api_id}", response_model=LetterSchema)
async def read_letter(letter_api_id: str, db: Session = Depends(get_db)) -> Letter:
    db_letter = api_identifier_crud.get_model(db, Letter, api_id=letter_api_id)
    return db_letter


@internal.post(
    "/letter/{letter_api_id}:add_question",
    response_model=LetterSchema,
)
async def add_question(
    letter_api_id: str, question: QuestionCreate, db: Session = Depends(get_db)
) -> Letter:
    db_letter = api_identifier_crud.get_model(db, Letter, api_id=letter_api_id)
    q = letter_crud.add_question(db, db_letter, question.question_text)
    db.refresh(db_letter)
    db.commit()
    return db_letter
