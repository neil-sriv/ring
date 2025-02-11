from __future__ import annotations

from typing import TYPE_CHECKING, Any

import factory

from ring.parties.models.group_model import Group
from ring.tests.factories.base_factory import BaseFactory, register_factory

if TYPE_CHECKING:
    from ring.parties.models.user_model import User


@register_factory
class GroupFactory(BaseFactory[Group]):
    class Meta:
        model = Group

    name = factory.Faker("pystr_format", string_format="Group-{{random_int}}")
    admin = factory.SubFactory(
        "ring.tests.factories.parties.user_factory.UserFactory"
    )

    @factory.post_generation
    def members(
        obj: Group, create: bool, extracted: list[User] | None, **kwargs: Any
    ):
        if extracted:
            assert obj.admin in extracted, "Admin must be a member"
            obj.members = extracted
