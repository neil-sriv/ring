from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterator
from ring.sqlalchemy_base import SessionLocal

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@dataclass
class RequestDependencies:
    db: Session


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_request_dependencies() -> RequestDependencies:
    return RequestDependencies(db=next(get_db()))
