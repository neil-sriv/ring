"""CRUD operations for user management.

This module provides functions for managing users in the database, including
authentication, creation, and retrieval operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Sequence

from sqlalchemy import select

from ring.parties.models.user_model import User
from ring.search.crud.hybrid_search import (
    create_hybrid_search_document,
    register_search_function,
)
from ring.search.models.hybrid_search import (
    HybridSearchDocument,
    SearchableType,
)
from ring.security import get_password_hash, verify_password

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> Optional[User]:
    """Authenticate a user with email and password.

    Args:
        db (Session): Database session
        email (str): User's email address
        password (str): User's password

    Returns:
        Optional[User]: Authenticated user or None if authentication fails
    """
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not _verify_password(password, user.hashed_password):
        return None
    return user


def _verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash.

    Args:
        password (str): Plain text password
        password_hash (str): Hashed password

    Returns:
        bool: True if password matches hash, False otherwise
    """
    return verify_password(password, password_hash)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by their email address.

    Args:
        db (Session): Database session
        email (str): Email address to look up

    Returns:
        Optional[User]: Found user or None
    """
    return db.scalars(select(User).filter(User.email == email)).one_or_none()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> Sequence[User]:
    """Get a list of users with pagination.

    Args:
        db (Session): Database session
        skip (int, optional): Number of records to skip. Defaults to 0.
        limit (int, optional): Maximum number of records to return. Defaults to 100.

    Returns:
        Sequence[User]: List of users
    """
    return db.scalars(select(User).offset(skip).limit(limit)).all()


@register_search_function(SearchableType.USER, User)
def create_user_search_document(
    db: Session, user: User
) -> HybridSearchDocument:
    """Create a search document for a user.

    Args:
        db (Session): Database session
        user (User): User to create a search document for

    Returns:
        HybridSearchDocument: Search document for the user
    """
    raw_text = f"{user.name} {user.email}"
    return create_hybrid_search_document(
        db, raw_text, user.api_identifier, SearchableType.USER
    )


def create_user(
    db: Session,
    email: str,
    name: str,
    password: str,
) -> User:
    """Create a new user.

    Args:
        db (Session): Database session
        email (str): User's email address
        name (str): User's display name
        password (str): User's password (will be hashed)

    Returns:
        User: Created user
    """
    hashed_password = get_password_hash(password)
    db_user = User.create(email, name, hashed_password)
    db.add(db_user)
    db.add(create_user_search_document(db, db_user))
    return db_user


def make_user_admin(db: Session, user: User) -> None:
    """Make a user an admin.

    Args:
        db (Session): Database session
        user (User): User to make admin
    """
    user.admin = True
