from secrets import token_urlsafe

import factory

from ring.parties.models.one_time_token_model import OneTimeToken, TokenType
from ring.tests.factories.base_factory import BaseFactory, register_factory


@register_factory
class OneTimeTokenFactory(BaseFactory[OneTimeToken]):
    class Meta:
        model = OneTimeToken

    token = factory.LazyAttribute(lambda _: token_urlsafe(32))
    type = TokenType.INVITE
    email = factory.Faker("email")
