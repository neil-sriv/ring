"""SQLAlchemy configuration and database utilities for Ring.

This module sets up SQLAlchemy with the database engine and session management.
It provides the base model class for all database models and utilities for
managing database sessions.
"""

from typing import Any, Callable, Iterator, TypeVar

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from ring.config import get_config

engine = create_engine(
    get_config().cockroach_database_uri,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models in Ring.

    All database models should inherit from this class to ensure they use
    the same declarative base and metadata.
    """

    pass


Base()


def get_db() -> Iterator[Session]:
    """Get a database session from the session pool.

    This is a generator function that yields a database session and ensures
    it is properly closed after use, even if an error occurs.

    Yields:
        Session: A SQLAlchemy database session

    Example:
        ```python
        db = next(get_db())
        try:
            # use db session
        finally:
            db.close()
        ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


T = TypeVar("T")


def db_session(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator that injects a database session into a function.

    This decorator wraps a function to automatically provide a database session
    as its first argument. It ensures the session is properly closed after use.

    Args:
        func (Callable[..., T]): Function to wrap with database session management

    Returns:
        Callable[..., T]: Wrapped function that automatically manages db sessions

    Example:
        ```python
        @db_session
        def get_user(db: Session, user_id: int) -> User:
            return db.query(User).get(user_id)
        ```
    """

    def wrapper(*args: Any, **kwargs: Any) -> T:
        """Wrapper function that manages the database session.

        Args:
            *args (Any): Positional arguments to pass to the wrapped function
            **kwargs (Any): Keyword arguments to pass to the wrapped function

        Returns:
            T: Return value from the wrapped function
        """
        db = next(get_db())
        try:
            return func(db, *args, **kwargs)
        finally:
            db.close()

    return wrapper
