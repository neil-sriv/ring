from __future__ import annotations

import factory

from ring.notifications.constants import NotificationType
from ring.notifications.models.notification import Notification
from ring.tests.factories.base_factory import BaseFactory, register_factory


@register_factory
class NotificationFactory(BaseFactory[Notification]):
    class Meta:
        model = Notification

    recipient = factory.SubFactory(
        "ring.tests.factories.parties.user_factory.UserFactory"
    )
    type = NotificationType.GENERIC
    title = factory.Faker("sentence", nb_words=4)
    body = factory.Faker("sentence", nb_words=8)
    target_api_id = None
