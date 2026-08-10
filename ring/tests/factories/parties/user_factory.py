from __future__ import annotations

from typing import Any

from factory import Faker, Sequence, post_generation

from ring.parties.models.user_model import User
from ring.security import get_password_hash
from ring.tests.factories.base_factory import BaseFactory, register_factory


DEFAULT_PASSWORD_HASH = get_password_hash("password")


@register_factory
class UserFactory(BaseFactory[User]):
    class Meta:
        model = User

    @post_generation
    def password(
        obj, create: bool, extracted: str | None, **kwargs: Any
    ) -> None:
        if extracted is None or extracted == "password":
            obj.hashed_password = DEFAULT_PASSWORD_HASH
        else:
            obj.hashed_password = get_password_hash(extracted)

    # Sequence avoids unique-constraint flakes on User.email (unique=True).
    email = Sequence(lambda n: f"user-{n}@example.com")
    name = Faker("name")

    # Temporary value until post generation function is called
    hashed_password = Faker("password")


@register_factory
class AdminFactory(UserFactory):
    @post_generation
    def admin(obj, create: bool, extracted: str | None, **kwargs: Any) -> None:
        obj.admin = True
