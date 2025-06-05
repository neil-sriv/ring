"""Test configuration and fixtures for Ring scripts.

This module provides test-specific fixtures for script testing, including
database sessions and script dependencies. It ensures proper setup and cleanup
of resources for script tests.
"""

from __future__ import annotations

from typing import Generator

import pytest
from sqlalchemy.orm import Session

from ring.scripts.dependencies import ScriptDependencies
from ring.tests.conftest import db_session


@pytest.fixture(scope="function")
def script_deps(
    db_session: Session,
) -> Generator[ScriptDependencies, None, None]:
    """Create script dependencies for testing.

    This fixture provides a ScriptDependencies instance configured with a test
    database session. It ensures proper cleanup of resources after each test.

    Args:
        db_session (Session): Test database session

    Yields:
        ScriptDependencies: Dependencies configured for script testing
    """
    deps = ScriptDependencies(db=db_session)
    yield deps
    # Cleanup if needed
    db_session.rollback()


@pytest.fixture(scope="function")
def script_deps_with_rollback(
    script_deps: ScriptDependencies,
) -> Generator[ScriptDependencies, None, None]:
    """Create script dependencies that automatically rollback changes.

    This fixture provides script dependencies that will automatically rollback
    any database changes made during the test. This is useful for tests that
    modify the database but should not persist those changes.

    Args:
        script_deps (ScriptDependencies): Base script dependencies

    Yields:
        ScriptDependencies: Dependencies configured for testing with rollback
    """
    yield script_deps
    script_deps.db.rollback()
