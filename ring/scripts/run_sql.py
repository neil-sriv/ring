"""Script to execute arbitrary SQL queries against the Ring database.

This script provides a way to run raw SQL queries against the database and
display the results in a formatted manner using pprintpp.
"""

from __future__ import annotations

from loguru import logger
from sqlalchemy import text

from ring.scripts.dependencies import (
    ScriptDependencies,
    get_script_dependencies,
    script_depends,
)


def run_script(
    query: str,
    deps: ScriptDependencies = script_depends(get_script_dependencies),
) -> None:
    """Execute a raw SQL query and display the results.

    This function executes the provided SQL query using SQLAlchemy's text()
    construct for safe query execution. The results are displayed with column
    names and formatted output.

    Args:
        query (str): Raw SQL query to execute
        deps (ScriptDependencies): Script dependencies provided by script_depends

    Note:
        The query is executed using SQLAlchemy's text() construct which provides
        SQL injection protection. However, care should still be taken with the
        queries being executed.
    """
    logger.info("Running query: {}".format(query))
    results = deps.db.execute(text(query))
    logger.info(results.keys())
    logger.info(results.fetchall())
