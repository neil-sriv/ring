"""Unit test configuration and fixtures for Ring.

This module provides unit test-specific fixtures for authentication and
client management. It extends the base test configuration with user-specific
test clients and authentication helpers.
"""

from typing import Callable, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.fastapp.dependencies import get_current_user
from ring.parties.models.user_model import User
from ring.tests.factories.parties.user_factory import AdminFactory, UserFactory

TClientForUser = Callable[[User], TestClient]


@pytest.fixture(scope="function")
def authenticated_client(
    request: pytest.FixtureRequest,
    get_client_for_user: TClientForUser,
    db_session: Session,
) -> Generator[TestClient, None, None]:
    """Create a test client with an authenticated user.

    This fixture creates a test client with a default authenticated user.
    The user is created using the UserFactory and committed to the database.

    Args:
        get_client_for_user (TClientForUser): Function to create a client for a specific user
        db_session (Session): Test database session

    Yields:
        TestClient: FastAPI test client instance with authentication
    """
    marker = request.node.get_closest_marker("admin")
    if marker:
        user = AdminFactory.create()
    else:
        user = UserFactory.create()
    db_session.commit()

    yield get_client_for_user(user)


@pytest.fixture(scope="function")
def get_client_for_user(
    unauthenticated_client: TestClient,
) -> Generator[TClientForUser, None, None]:
    """Create a function to generate authenticated test clients.

    This fixture provides a function that can create test clients for any user.
    It manages the dependency overrides for user authentication.

    Args:
        unauthenticated_client (TestClient): Base test client without authentication

    Yields:
        TClientForUser: Function that creates an authenticated client for a specific user
    """

    def _method(user: User):
        unauthenticated_client.app.dependency_overrides[get_current_user] = (
            lambda: user
        )
        return unauthenticated_client

    yield _method
    unauthenticated_client.app.dependency_overrides.pop(get_current_user)


@pytest.fixture(scope="function")
def current_user(authenticated_client: TestClient) -> User:
    """Get the current authenticated user from the test client.

    This fixture retrieves the user that was used to create the authenticated client.

    Args:
        authenticated_client (TestClient): Test client with authentication

    Returns:
        User: The currently authenticated user
    """
    return authenticated_client.app.dependency_overrides[get_current_user]()
