from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class SubscriptionBase(BaseModel):
    """Base schema for web push notification subscriptions.

    :param endpoint: Push notification endpoint URL
    :type endpoint: str
    :param keys: Dictionary containing encryption keys and auth info
    :type keys: dict[str, str | float | bool]
    """
    endpoint: str
    keys: dict[str, str | float | bool]


class SubscriptionCreate(SubscriptionBase):
    """Schema for creating a new subscription.

    Inherits endpoint and keys from SubscriptionBase and adds user identification.

    :param endpoint: Push notification endpoint URL
    :type endpoint: str
    :param keys: Dictionary containing encryption keys and auth info
    :type keys: dict[str, str | float | bool]
    :param user_api_identifier: API identifier of the user to subscribe
    :type user_api_identifier: str
    """
    user_api_identifier: str


class Subscription(SubscriptionBase):
    """Schema representing a subscription in the system.

    Inherits endpoint and keys from SubscriptionBase and adds system fields.

    :param endpoint: Push notification endpoint URL
    :type endpoint: str
    :param keys: Dictionary containing encryption keys and auth info
    :type keys: dict[str, str | float | bool]
    :param api_identifier: Unique API identifier for the subscription
    :type api_identifier: str
    """
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str
