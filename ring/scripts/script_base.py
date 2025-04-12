"""Base functionality for Ring scripts.

This module provides decorators and base functions for creating database-aware
scripts that can be run through the script runner.
"""
from __future__ import annotations

import functools
from typing import Any, Callable

from ring.sqlalchemy_base import Session, T, db_session


def script_di() -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Create a decorator for dependency injection in scripts.

    This decorator wraps script functions to provide database session management
    and other dependencies. It ensures proper setup and cleanup of resources.

    Returns:
        Callable: A decorator that can be applied to script functions
    """

    def decorator(f: Callable[..., T]) -> Callable[..., T]:
        """Wrap a script function with database session management.

        Args:
            f (Callable[..., T]): The script function to wrap

        Returns:
            Callable[..., T]: The wrapped function with database session management
        """

        @db_session
        @functools.wraps(f)
        def inner(db: Session, *args: Any, **kwargs: Any) -> T:
            return f(db, *args, **kwargs)

        return inner

    return decorator


@script_di()
def run_script(db: Session, dry_run: bool = True) -> None:
    """Base script function to be overridden by actual scripts.

    Args:
        db (Session): Database session provided by the decorator
        dry_run (bool): Whether to perform a dry run
    """
    raise NotImplementedError()
