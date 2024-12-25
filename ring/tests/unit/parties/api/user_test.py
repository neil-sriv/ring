import sqlalchemy
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ring.parties.models.user_model import User
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.invite_factory import InviteFactory
from ring.tests.factories.parties.one_time_token_factory import (
    OneTimeTokenFactory,
)
from ring.tests.factories.parties.user_factory import UserFactory
from ring.tests.lib.utils import (
    assert_pydantic_model_json_dump_equivalent_to_response_dict,
    assert_pydantic_models_json_dump_in_response_dict,
)
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

    def test_register_user(
        self,
        unauthenticated_client: TestClient,
        faker: Faker,
        db_session: Session,
    ) -> None:
        invite = InviteFactory.create()
        db_session.commit()

        email, name, password = invite.email, faker.name(), faker.password()

        input = {
            "email": email,
            "name": name,
            "password": password,
        }
        resp = unauthenticated_client.post(
            f"/parties/register/{invite.one_time_token.token}", json=input
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data == data | {
            "email": email,
            "name": name,
        }

        db_user = db_session.scalar(
            sqlalchemy.select(User).where(User.email == email)
        )
        assert db_user
        assert db_user.email == email
        assert db_user.name == name

        assert db_user in invite.group.members

        assert invite.one_time_token.used

    def test_register_user_invalid_token(
        self,
        unauthenticated_client: TestClient,
        faker: Faker,
        db_session: Session,
    ) -> None:
        input = {
            "email": faker.email(),
            "name": faker.name(),
            "password": faker.password(),
        }
        resp = unauthenticated_client.post(
            "/parties/register/invalid_token", json=input
        )

        assert resp.status_code == 400
        assert resp.json()["detail"] == "Invalid token"

        expired_token = OneTimeTokenFactory.create()
        expired_token.ttl = 0
        db_session.commit()

        resp = unauthenticated_client.post(
            f"/parties/register/{expired_token.token}", json=input
        )

        assert resp.status_code == 400
        assert resp.json()["detail"] == "Invalid token"

        used_token = OneTimeTokenFactory.create()
        used_token.used = True
        db_session.commit()

        resp = unauthenticated_client.post(
            f"/parties/register/{used_token.token}", json=input
        )

        assert resp.status_code == 400
        assert resp.json()["detail"] == "Invalid token"

    def test_register_user_email_mismatch(
        self,
        unauthenticated_client: TestClient,
        faker: Faker,
        db_session: Session,
    ) -> None:
        invite = InviteFactory.create(email="invite_email")
        db_session.commit()

        input = {
            "email": "different_email",
            "name": faker.name(),
            "password": faker.password(),
        }
        resp = unauthenticated_client.post(
            f"/parties/register/{invite.one_time_token.token}", json=input
        )

        assert resp.status_code == 400
        assert resp.json()["detail"] == "Email mismatch"

    def test_register_user_duplicate(
        self,
        unauthenticated_client: TestClient,
        faker: Faker,
        db_session: Session,
    ) -> None:
        invite = InviteFactory.create()
        db_session.commit()

        user = UserFactory.create(email=invite.email)
        db_session.commit()

        input = {
            "email": user.email,
            "name": faker.name(),
            "password": faker.password(),
        }
        resp = unauthenticated_client.post(
            f"/parties/register/{invite.one_time_token.token}", json=input
        )

        assert resp.status_code == 400
        assert resp.json()["detail"] == "Email already registered"

    def test_read_users(
        self,
        authenticated_client: TestClient,
        db_session: Session,
        current_user: User,
    ) -> None:
        users = [UserFactory.create() for _ in range(5)]
        group = GroupFactory.create(admin=current_user)
        group_users = [UserFactory.create() for _ in range(5)]
        for user in group_users:
            group.members.append(user)
        db_session.commit()

        resp = authenticated_client.get("/parties/users")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 11  # 10 users + current user
        assert_pydantic_models_json_dump_in_response_dict(
            users + group_users + [current_user], data
        )

    def test_read_user_by_id(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        user = UserFactory.create()
        db_session.commit()

        resp = authenticated_client.get(f"/parties/user/{user.api_identifier}")
        assert resp.status_code == 200
        data = resp.json()
        print(data)
        assert_pydantic_model_json_dump_equivalent_to_response_dict(user, data)

    def test_read_user_by_id_not_found(
        self,
        authenticated_client: TestClient,
    ) -> None:
        resp = authenticated_client.get("/parties/user/invalid_id")
        assert resp.status_code == 404
        assert (
            resp.json()["detail"]
            == 'Could not resolve "invalid_id" for model class User'
        )

    def test_update_user_me_name(
        self,
        authenticated_client: TestClient,
        current_user: User,
        faker: Faker,
    ) -> None:
        new_name = faker.name()
        assert current_user.name != new_name
        input = {"name": new_name}
        resp = authenticated_client.patch("/parties/me", json=input)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == new_name
        assert current_user.name == new_name

    def test_update_user_me_email(
        self,
        authenticated_client: TestClient,
        current_user: User,
        faker: Faker,
    ) -> None:
        new_email = faker.email()
        assert current_user.email != new_email
        input = {"email": new_email}
        resp = authenticated_client.patch("/parties/me", json=input)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == new_email
        assert current_user.email == new_email

    def test_update_user_me_email_duplicate(
        self,
        authenticated_client: TestClient,
        db_session: Session,
    ) -> None:
        user = UserFactory.create()
        db_session.commit()

        input = {"email": user.email}
        resp = authenticated_client.patch("/parties/me", json=input)
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Email already registered"

    def test_update_user_me_password(
        self,
        authenticated_client: TestClient,
        faker: Faker,
    ) -> None:
        new_password = faker.password()
        input = {
            "current_password": "password",
            "new_password": new_password,
        }
        resp = authenticated_client.patch("/parties/me/password", json=input)
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "Password updated successfully"

    def test_update_user_me_password_incorrect_password(
        self,
        authenticated_client: TestClient,
        faker: Faker,
    ) -> None:
        new_password = faker.password()
        input = {
            "current_password": "incorrect_password",
            "new_password": new_password,
        }
        resp = authenticated_client.patch("/parties/me/password", json=input)
        assert resp.status_code == 400
        assert resp.json()["detail"] == "Incorrect password"

    def test_update_user_me_password_same_password(
        self,
        authenticated_client: TestClient,
    ) -> None:
        input = {
            "current_password": "password",
            "new_password": "password",
        }
        resp = authenticated_client.patch("/parties/me/password", json=input)
        assert resp.status_code == 400
        assert (
            resp.json()["detail"]
            == "New password must be different from the current password"
        )

    assert False
