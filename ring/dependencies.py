from __future__ import annotations
from typing import TYPE_CHECKING, Iterator
from ring.sqlalchemy_base import SessionLocal

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
