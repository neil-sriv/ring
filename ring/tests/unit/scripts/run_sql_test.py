"""Tests for the run_sql script.

This module provides tests for the run_sql script, ensuring it correctly
executes SQL queries and handles results appropriately.
"""

from __future__ import annotations

from sqlalchemy import text

from ring.scripts.dependencies import ScriptDependencies
from ring.scripts.run_sql import run_script
from ring.tests.unit.scripts.script_tester import ScriptTestBase


class TestRunSql(ScriptTestBase):
    """Test cases for the run_sql script."""

    def test_run_simple_select(self, script_deps: ScriptDependencies):
        """Test that the script correctly executes a simple SELECT query.

        Args:
            script_deps (ScriptDependencies): Script dependencies with test database session
        """
        # Create a test table and insert data
        script_deps.db.execute(
            text("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        """)
        )
        script_deps.db.execute(
            text("""
            INSERT INTO test_table (id, name) VALUES 
            (1, 'test1'),
            (2, 'test2')
        """)
        )
        script_deps.db.commit()

        # Run the script with a simple SELECT query
        query = "SELECT * FROM test_table ORDER BY id"
        rv = self.run(run_script, query=query, deps=script_deps)

        # Verify results
        assert rv is None  # The function returns None as it logs results
