import factory

from ring.parties.models.invite_model import Invite
from ring.tests.factories.base_factory import BaseFactory, register_factory


@register_factory
class InviteFactory(BaseFactory[Invite]):
    class Meta:
        model = Invite

    email = factory.Faker("email")
    inviter = factory.SubFactory(
        "ring.tests.factories.parties.user_factory.UserFactory"
    )
    group = factory.SubFactory(
        "ring.tests.factories.parties.group_factory.GroupFactory"
    )
    token = factory.SubFactory(
        "ring.tests.factories.parties.one_time_token_factory.OneTimeTokenFactory"
    )
