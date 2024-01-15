from __future__ import annotations
from fastapi import Depends, HTTPException
from ring.dependencies import get_db
from typing import TYPE_CHECKING, Sequence
from ring.crud import letter as letter_crud, api_identifier as api_identifier_crud
from ring.pydantic_schemas.schemas import Letter as LetterSchema, LetterCreate
from ring.routes import internal

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from ring.postgres_models.letter_model import Letter


@internal.post("/letter", response_model=LetterSchema)
def add_next_letter(letter: LetterCreate, db: Session = Depends(get_db)) -> Letter:
    return letter_crud.create_letter(db=db, letter=letter)


@internal.get("/letters/", response_model=Sequence[LetterSchema])
def list_letters(
    group_api_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> Sequence[Letter]:
    letters = letter_crud.get_letters(
        db, group_api_id=group_api_id, skip=skip, limit=limit
    )
    return letters


@internal.get("/letter/{letter_api_id}", response_model=LetterSchema)
def read_letter(letter_api_id: str, db: Session = Depends(get_db)) -> Letter:
    db_letter = api_identifier_crud.get_model(db, Letter, api_id=letter_api_id)
    if db_letter is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_letter