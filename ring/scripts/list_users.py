"""Script to list all users in the Ring database.

This script retrieves and displays all users from the database using SQLAlchemy.
"""
from __future__ import annotations

from sqlalchemy import select

from ring.parties.models.user_model import User
from ring.scripts.script_base import script_di
from ring.sqlalchemy_base import Session


@script_di()
def run_script(db: Session) -> None:
    """List all users in the database.

    Executes a simple query to retrieve all users and prints them to stdout.
    Uses SQLAlchemy's select statement for efficient querying.

    Args:
        db (Session): Database session provided by script_di
    """
    users = db.scalars(select(User)).all()
    print(users)
