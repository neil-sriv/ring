import sqlalchemy
from faker import Faker
from sqlalchemy.orm import Session

from ring.parties.crud.user import get_password_hash
from ring.parties.models.user_model import User
from ring.tests.factories.letters.response_factory import ResponseFactory
from ring.tests.factories.parties.group_factory import GroupFactory


class TestUserModel:
    def test_user_model(self, faker: Faker, db_session: Session) -> None:
        hashed_password = get_password_hash("password")
        email = faker.email()
        user = User.create(
            email=email, name="test", hashed_password=hashed_password
        )
        db_session.add(user)
        db_session.commit()

        assert user.email == email
        assert user.name == "test"
        assert user.hashed_password == hashed_password
        assert user.api_identifier.startswith(User.API_ID_PREFIX)
        assert user.id is not None
        assert user.created_at is not None

        db_user = db_session.scalars(
            sqlalchemy.select(User).filter(User.email == email)
        ).one()
        assert db_user == user

    def test_user_model_with_group(
        self, faker: Faker, db_session: Session
    ) -> None:
        hashed_password = get_password_hash("password")
        email = faker.email()
        user = User(email=email, name="test", hashed_password=hashed_password)
        db_session.add(user)
        db_session.commit()

        assert user.groups == []

        group = GroupFactory.create()
        user.groups = [group]
        db_session.commit()

        assert user.groups == [group]

    def test_user_model_with_response(
        self, faker: Faker, db_session: Session
    ) -> None:
        hashed_password = get_password_hash("password")
        email = faker.email()
        user = User(email=email, name="test", hashed_password=hashed_password)
        db_session.add(user)
        db_session.commit()

        assert user.responses == []

        response = ResponseFactory.create(participant=user)
        db_session.commit()

        assert user.responses == [response]
