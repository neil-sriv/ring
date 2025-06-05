"""Tests for the backfill_user_admins script.

This module provides tests for the backfill_user_admins script, ensuring it correctly
sets admin status for specified users.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from ring.parties.models.user_model import User
from ring.scripts.dependencies import ScriptDependencies
from ring.scripts.parties.backfill_user_admins import run_script
from ring.tests.factories.parties.user_factory import UserFactory
from ring.tests.unit.scripts.script_tester import ScriptTestBase


class TestBackfillUserAdmins(ScriptTestBase):
    """Test cases for the backfill_user_admins script."""

    def test_make_users_admin(self, script_deps: ScriptDependencies):
        """Test that the script correctly sets admin status for users.

        Args:
            script_deps (ScriptDependencies): Script dependencies with test database session
        """
        # Create test users
        users = [
            UserFactory.create(email=f"user{i}@test.com") for i in range(3)
        ]
        script_deps.db.add_all(users)
        script_deps.db.commit()

        # Run the script with dry_run=True
        self.run(
            run_script,
            user_emails=[user.email for user in users],
            dry_run=True,
            deps=script_deps,
        )

        # Get fresh copies of users from database after rollback
        users = script_deps.db.scalars(
            select(User).where(
                User.email.in_([f"user{i}@test.com" for i in range(3)])
            )
        ).all()

        # Verify no changes were made (due to dry run)
        for user in users:
            assert not user.admin

        # Run the script with dry_run=False
        self.run(
            run_script,
            user_emails=[user.email for user in users],
            dry_run=False,
            deps=script_deps,
        )

        # Verify users were made admin
        for user in users:
            assert user.admin

    def test_missing_user(self, script_deps: ScriptDependencies):
        """Test that the script handles missing users gracefully.

        Args:
            script_deps (ScriptDependencies): Script dependencies with test database session
        """
        # Create one test user
        user = UserFactory.create(email="user@test.com")
        script_deps.db.add(user)
        script_deps.db.commit()

        # Run the script with one existing and one missing user
        self.run(
            run_script,
            user_emails=["user@test.com", "nonexistent@test.com"],
            dry_run=False,
            deps=script_deps,
        )

        # Verify only existing user was made admin
        assert user.admin

    def test_missing_user_emails(self, script_deps: ScriptDependencies):
        """Test that the script raises an error when user_emails is not provided.

        Args:
            script_deps (ScriptDependencies): Script dependencies with test database session
        """
        # Run the script without user_emails
        with pytest.raises(ValueError, match="user_emails is required"):
            self.run(run_script, dry_run=False, deps=script_deps)
