from typing import Callable, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.dependencies import get_current_user
from ring.parties.models.user_model import User
from ring.tests.factories.parties.user_factory import UserFactory

TClientForUser = Callable[[User], TestClient]


@pytest.fixture(scope="function")
def authenticated_client(
    get_client_for_user: TClientForUser, db_session: Session
) -> Generator[TestClient, None, None]:
    user = UserFactory.create()
    db_session.commit()

    yield get_client_for_user(user)


@pytest.fixture(scope="function")
def get_client_for_user(
    client: TestClient,
) -> Generator[TClientForUser, None, None]:
    def _method(user: User):
        client.app.dependency_overrides[get_current_user] = lambda: user
        return client

    yield _method
    client.app.dependency_overrides.pop(get_current_user)


@pytest.fixture(scope="function")
def current_user(authenticated_client: TestClient) -> User:
    return authenticated_client.app.dependency_overrides[get_current_user]()
