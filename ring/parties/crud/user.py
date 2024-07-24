from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Sequence

from sqlalchemy import select
from ring.postgres_models import User
from ring.security import get_password_hash, verify_password

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not _verify_password(password, user.hashed_password):
        return None
    return user


def _verify_password(password: str, password_hash: str) -> bool:
    return verify_password(password, password_hash)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.scalars(select(User).filter(User.email == email)).one_or_none()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> Sequence[User]:
    return db.scalars(select(User).offset(skip).limit(limit)).all()


def create_user(
    db: Session,
    email: str,
    name: str,
    password: str,
) -> User:
    hashed_password = get_password_hash(password)
    db_user = User.create(email, name, hashed_password)
    db.add(db_user)
    return db_user
