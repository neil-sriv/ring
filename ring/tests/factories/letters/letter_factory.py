from datetime import UTC, datetime, timedelta
from typing import Any

import factory

from ring.letters.constants import LetterStatus
from ring.letters.crud.letter import upsert_letter_tasks
from ring.letters.models.letter_model import Letter
from ring.tests.factories.base_factory import BaseFactory, register_factory


@register_factory
class LetterFactory(BaseFactory[Letter]):
    class Meta:
        model = Letter

    @factory.post_generation
    def _schedule(
        obj: Letter, create: bool, extracted: str | None, **kwargs: Any
    ):
        upsert_letter_tasks(
            LetterFactory._meta.sqlalchemy_session,
            obj,
            obj.send_at,
        )

    send_at = factory.LazyFunction(
        lambda: datetime.now(tz=UTC) + timedelta(days=2)
    )
    status = LetterStatus.IN_PROGRESS
    group = factory.SubFactory(
        "ring.tests.factories.parties.group_factory.GroupFactory"
    )
