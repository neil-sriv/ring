"""Script dependency injection utilities for Ring.

This module provides dependency injection utilities for Ring scripts, similar to
FastAPI's dependency injection system but designed for standalone script execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, TypeVar

from ring.sqlalchemy_base import Session, get_db

T = TypeVar("T")


@dataclass
class ScriptDependencies:
    """Base class for script dependencies.

    This class provides the basic dependencies needed for any script,
    such as database sessions.

    Attributes:
        db (Session): SQLAlchemy database session
    """

    db: Session


def get_script_dependencies() -> ScriptDependencies:
    """Get dependencies for script execution.

    This function provides a database session for script execution.

    Returns:
        ScriptDependencies: Basic script dependencies
    """
    db = next(get_db())
    return ScriptDependencies(db=db)


def script_depends(dependency: Callable[..., Any]) -> Any:
    """Create a dependency for script functions.

    This decorator works similarly to FastAPI's Depends but for standalone scripts.
    It ensures proper setup and cleanup of resources.

    Args:
        dependency (Callable[..., Any]): The dependency function to call

    Returns:
        Any: The result of calling the dependency function
    """
    return dependency()
