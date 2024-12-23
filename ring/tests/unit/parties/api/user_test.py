import sqlalchemy
from factory.faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.parties.models.user_model import User
from ring.tests.factories.parties.user_factory import UserFactory
from ring.tests.unit.parties.conftest import TClientForUser


class TestUserAPI:
    def test_read_me_authenticated(
        self, get_client_for_user: TClientForUser, db_session: Session
    ):
        user = UserFactory.create(email="test@gmail.com")
        db_session.commit()
        client = get_client_for_user(user)
        response = client.get("/parties/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@gmail.com"

    def test_read_me_unauthenticated(self, unauthenticated_client: TestClient):
        response = unauthenticated_client.get("/parties/me")
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Not authenticated"

    def test_create_user(
        self,
        unauthenticated_client: TestClient,
        faker: Faker,
        db_session: Session,
    ) -> None:
        email, name, password = faker.email(), faker.name(), faker.password()
        input: dict[str, str] = {
            "email": email,
            "name": name,
            "password": password,
        }
        resp = unauthenticated_client.post("/parties/user", json=input)

        assert resp.status_code == 201
        data = resp.json()
        assert data == data | {
            "email": email,
            "name": name,
        }
        assert db_session.scalar(
            sqlalchemy.select(User).where(User.email == email)
        )

    def test_create_user_duplicate(
        self,
        unauthenticated_client: TestClient,
        db_session: Session,
        faker: Faker,
    ) -> None:
        db_user = UserFactory.create()
        db_session.commit()

        input: dict[str, str] = {
            "email": db_user.email,
            "name": db_user.name or "name",
            "password": faker.password(),
        }
        resp = unauthenticated_client.post("/parties/user", json=input)

        assert resp.status_code == 400
        assert resp.json()["detail"] == "Email already registered"
