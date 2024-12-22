from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.tests.factories.parties.user_factory import UserFactory
from ring.tests.unit.parties.conftest import TClientForUser


def test_get_me_authenticated(
    get_client_for_user: TClientForUser, db_session: Session
):
    user = UserFactory.create(email="test@gmail.com")
    db_session.commit()
    client = get_client_for_user(user)
    response = client.get("/api/v1/parties/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@gmail.com"


def test_get_me_unauthenticated(client: TestClient):
    response = client.get("/api/v1/parties/me")
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Not authenticated"
