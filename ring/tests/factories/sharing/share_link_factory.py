from __future__ import annotations

import factory

from ring.sharing.crud.share_link import generate_share_token
from ring.sharing.models.share_link_model import ShareLink
from ring.tests.factories.base_factory import BaseFactory, register_factory


@register_factory
class ShareLinkFactory(BaseFactory[ShareLink]):
    class Meta:
        model = ShareLink

    token = factory.LazyFunction(generate_share_token)
    target_api_id = factory.Sequence(lambda n: f"lttr_share-target-{n}")
    created_by_api_id = factory.Sequence(lambda n: f"usr_share-creator-{n}")
