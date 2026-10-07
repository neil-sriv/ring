from __future__ import annotations

import factory

from ring.notifications.models.inbox_item import InboxItem
from ring.tests.factories.base_factory import BaseFactory, register_factory


@register_factory
class InboxItemFactory(BaseFactory[InboxItem]):
    class Meta:
        model = InboxItem

    title = "New letter"
    body = "A letter is ready to read"
    target_api_id = "lttr_example"
    user = factory.SubFactory(
        "ring.tests.factories.parties.user_factory.UserFactory"
    )
