from __future__ import annotations

import factory

from ring.links.models.short_link_model import ShortLink
from ring.tests.factories.base_factory import BaseFactory, register_factory
from ring.tests.factories.letters.letter_factory import LetterFactory


@register_factory
class ShortLinkFactory(BaseFactory[ShortLink]):
    class Meta:
        model = ShortLink

    creator = factory.SubFactory(
        "ring.tests.factories.parties.user_factory.UserFactory"
    )
    # Default to sharing a freshly created letter; override target_api_id to
    # point at any other resource.
    target_api_id = factory.LazyFunction(
        lambda: LetterFactory.create().api_identifier
    )
