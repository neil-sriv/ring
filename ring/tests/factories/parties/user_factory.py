from typing import Any

from factory import Faker, post_generation

from ring.parties.models.user_model import User
from ring.security import get_password_hash
from ring.tests.factories.base_factory import BaseFactory


class UserFactory(BaseFactory[User]):
    class Meta:
        model = User
        sqlalchemy_session_persistence = "flush"

    @post_generation
    def password(
        obj, create: bool, extracted: str | None, **kwargs: Any
    ) -> None:
        password = extracted or "password"
        obj.hashed_password = get_password_hash(password)

    email = Faker("email")
    name = Faker("name")

    # Temporary value until post generation function is called
    hashed_password = Faker("password")
