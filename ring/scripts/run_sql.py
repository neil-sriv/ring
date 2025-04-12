"""Script to execute arbitrary SQL queries against the Ring database.

This script provides a way to run raw SQL queries against the database and
display the results in a formatted manner using pprintpp.
"""
from __future__ import annotations

from pprintpp import pprint  # type: ignore
from sqlalchemy import text

from ring.scripts.script_base import script_di
from ring.sqlalchemy_base import Session


@script_di()
def run_script(db: Session, query: str) -> None:
    """Execute a raw SQL query and display the results.

    This function executes the provided SQL query using SQLAlchemy's text()
    construct for safe query execution. The results are displayed with column
    names and formatted output.

    Args:
        db (Session): Database session provided by script_di
        query (str): Raw SQL query to execute

    Note:
        The query is executed using SQLAlchemy's text() construct which provides
        SQL injection protection. However, care should still be taken with the
        queries being executed.
    """
    print(f"Running query: {query}")
    results = db.execute(text(query))
    pprint(results.keys())
    pprint(results.fetchall())
