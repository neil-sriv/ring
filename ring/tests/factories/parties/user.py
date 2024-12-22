from factory import Faker

from ring.parties.models.user_model import User
from ring.tests.factories.base_factory import BaseFactory


class UserFactory(BaseFactory[User]):
    class Meta:
        model = User
        sqlalchemy_session_persistence = "flush"

    email = Faker("email")
    name = Faker("name")
    hashed_password = Faker("password")
