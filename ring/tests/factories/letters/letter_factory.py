from datetime import UTC, datetime, timedelta

import factory

from ring.letters.constants import LetterStatus
from ring.letters.models.letter_model import Letter
from ring.tests.factories.base_factory import BaseFactory, register_factory


@register_factory
class LetterFactory(BaseFactory[Letter]):
    class Meta:
        model = Letter

    send_at = factory.LazyFunction(
        lambda: datetime.now(tz=UTC) + timedelta(days=1)
    )
    status = LetterStatus.IN_PROGRESS
    group = factory.SubFactory(
        "ring.tests.factories.parties.group_factory.GroupFactory"
    )
