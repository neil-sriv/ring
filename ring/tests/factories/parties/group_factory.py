import factory

from ring.parties.models.group_model import Group
from ring.tests.factories.base_factory import BaseFactory, register_factory


@register_factory
class GroupFactory(BaseFactory[Group]):
    class Meta:
        model = Group

    name = factory.Faker("name")
    admin = factory.SubFactory(
        "ring.tests.factories.parties.user_factory.UserFactory"
    )
