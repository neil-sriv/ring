"""Script to list all users in the Ring database.

This script retrieves and displays all users from the database using SQLAlchemy.
"""

from __future__ import annotations

from loguru import logger
from sqlalchemy import select

from ring.parties.models.user_model import User
from ring.scripts.dependencies import (
    ScriptDependencies,
    get_script_dependencies,
    script_depends,
)


def run_script(
    deps: ScriptDependencies = script_depends(get_script_dependencies),
) -> list[User]:
    """List all users in the database.

    Executes a simple query to retrieve all users and prints them to stdout.
    Uses SQLAlchemy's select statement for efficient querying.

    Args:
        deps (ScriptDependencies): Script dependencies provided by script_depends

    Returns:
        list[User]: List of all users in the database
    """
    users = deps.db.scalars(select(User)).all()
    logger.info(users)
    return users
