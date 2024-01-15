from __future__ import annotations
from fastapi import Depends
from ring.dependencies import get_db
from typing import TYPE_CHECKING
from ring.crud import letter as letter_crud
from ring.pydantic_schemas.schemas import Letter as LetterSchema, LetterCreate
from ring.routes import internal

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from ring.postgres_models.letter_model import Letter


@internal.post("/letter", response_model=LetterSchema)
def add_next_letter(letter: LetterCreate, db: Session = Depends(get_db)) -> Letter:
    return letter_crud.create_letter(db=db, letter=letter)
