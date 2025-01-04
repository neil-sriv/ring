from faker import Faker
from sqlalchemy.orm import Session

from ring.parties.crud import user as user_crud
from ring.tests.factories.parties.user_factory import UserFactory


class TestUserCrud:
    def test_get_users(self, db_session: Session) -> None:
        assert user_crud.get_users(db_session) == []

        db_users = [UserFactory.create() for _ in range(10)]
        db_session.commit()

        users = user_crud.get_users(db_session)
        assert len(users) == 10
        assert users == db_users

    def test_authenticate_user(self, db_session: Session) -> None:
        user = UserFactory.create(password="test password")
        db_session.commit()

        assert user == user_crud.authenticate_user(
            db_session, user.email, "test password"
        )

    def test_authenticate_user_invalid(self, db_session: Session) -> None:
        user = UserFactory.create(password="test password")
        db_session.commit()

        assert (
            user_crud.authenticate_user(
                db_session, user.email, "invalid password"
            )
            is None
        )
        assert (
            user_crud.authenticate_user(
                db_session, "invalid email", "test password"
            )
            is None
        )

    def test_get_user_by_email(self, db_session: Session) -> None:
        user = UserFactory.create(email="test_email")
        db_session.commit()

        assert user_crud.get_user_by_email(db_session, "test_email") == user

    def test_get_user_by_email_invalid(self, db_session: Session) -> None:
        UserFactory.create()
        db_session.commit()

        assert user_crud.get_user_by_email(db_session, "invalid_email") is None

    def test_create_user(self, db_session: Session, faker: Faker) -> None:
        email, name, password = faker.email(), faker.name(), faker.password()
        user = user_crud.create_user(db_session, email, name, password)
        db_session.commit()

        assert user.email == email
        assert user.name == name
        assert user_crud.authenticate_user(db_session, user.email, password)
