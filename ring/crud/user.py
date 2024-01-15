from __future__ import annotations
from typing import TYPE_CHECKING, Optional
from ring.postgres_models import User
from ring.pydantic_schemas.schemas import UserCreate

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).one_or_none()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, user: UserCreate) -> User:
    db_user = User.create(user.email, user.name, user.hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
