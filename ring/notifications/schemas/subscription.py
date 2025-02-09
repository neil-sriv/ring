from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class SubscriptionBase(BaseModel):
    endpoint: str
    keys: dict[str, str | float | bool]


class SubscriptionCreate(SubscriptionBase):
    user_api_identifier: str


class Subscription(SubscriptionBase):
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str
