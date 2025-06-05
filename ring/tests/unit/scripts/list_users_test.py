"""Tests for the list_users script.

This module provides tests for the list_users script, ensuring it correctly
retrieves and displays users from the database.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from ring.scripts.dependencies import ScriptDependencies
from ring.scripts.list_users import run_script
from ring.tests.factories.parties.user_factory import UserFactory
from ring.tests.unit.scripts.script_tester import ScriptTestBase


class TestListUsers(ScriptTestBase):
    """Test cases for the list_users script."""

    def test_list_users(self, script_deps: ScriptDependencies):
        """Test that the script correctly lists all users.

        Args:
            script_deps (ScriptDependencies): Script dependencies with test database session
        """
        # Create test users
        users = [UserFactory.create() for _ in range(1)]
        script_deps.db.add_all(users)
        script_deps.db.commit()

        # Run the script with test dependencies
        rv = self.run(run_script, deps=script_deps)

        # Verify results
        assert [
            user.to_pydantic().model_dump(mode="json") for user in users
        ] == [user.to_pydantic().model_dump(mode="json") for user in rv]
