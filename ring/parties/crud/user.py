"""CRUD operations for user management."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Sequence

from sqlalchemy import select

from ring.parties.models.user_model import User
from ring.security import get_password_hash, verify_password

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> Optional[User]:
    """Authenticate a user with email and password.

    :param db: Database session
    :type db: Session
    :param email: User's email address
    :type email: str
    :param password: User's password
    :type password: str
    :return: Authenticated user or None if authentication fails
    :rtype: Optional[User]
    """
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not _verify_password(password, user.hashed_password):
        return None
    return user


def _verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash.

    :param password: Plain text password
    :type password: str
    :param password_hash: Hashed password
    :type password_hash: str
    :return: True if password matches hash, False otherwise
    :rtype: bool
    """
    return verify_password(password, password_hash)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by their email address.

    :param db: Database session
    :type db: Session
    :param email: Email address to look up
    :type email: str
    :return: Found user or None
    :rtype: Optional[User]
    """
    return db.scalars(select(User).filter(User.email == email)).one_or_none()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> Sequence[User]:
    """Get a list of users with pagination.

    :param db: Database session
    :type db: Session
    :param skip: Number of records to skip, defaults to 0
    :type skip: int, optional
    :param limit: Maximum number of records to return, defaults to 100
    :type limit: int, optional
    :return: List of users
    :rtype: Sequence[User]
    """
    return db.scalars(select(User).offset(skip).limit(limit)).all()


def create_user(
    db: Session,
    email: str,
    name: str,
    password: str,
) -> User:
    """Create a new user.

    :param db: Database session
    :type db: Session
    :param email: User's email address
    :type email: str
    :param name: User's display name
    :type name: str
    :param password: User's password (will be hashed)
    :type password: str
    :return: Created user
    :rtype: User
    """
    hashed_password = get_password_hash(password)
    db_user = User.create(email, name, hashed_password)
    db.add(db_user)
    return db_user
