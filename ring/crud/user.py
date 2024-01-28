from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Sequence

from sqlalchemy import select
from ring.postgres_models import User
from ring.pydantic_schemas.user import UserCreate

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.scalars(select(User).filter(User.email == email)).one_or_none()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> Sequence[User]:
    return db.scalars(select(User).offset(skip).limit(limit)).all()


def create_user(db: Session, email: str, name: str, hashed_password: str) -> User:
    db_user = User.create(email, name, hashed_password)
    db.add(db_user)
    return db_user
