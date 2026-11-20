"""Pydantic schemas for web push notification subscriptions.

This module provides Pydantic models for validating and serializing web push
notification subscription data.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SubscriptionBase(BaseModel):
    """Base schema for web push notification subscriptions.

    Attributes:
        endpoint (str): Push notification endpoint URL
        keys (dict[str, str | float | bool]): Dictionary containing encryption keys and auth info
    """

    endpoint: str
    keys: dict[str, str | float | bool]


class SubscriptionCreate(SubscriptionBase):
    """Schema for creating a new subscription.

    Inherits endpoint and keys from SubscriptionBase. The subscribed user is
    the authenticated caller. ``user_api_identifier`` is deprecated.

    Attributes:
        endpoint (str): Push notification endpoint URL
        keys (dict[str, str | float | bool]): Dictionary containing encryption keys and auth info
        user_api_identifier (str | None): Deprecated. Omit it, or send the
            caller's id. Another user's id is rejected.
    """

    # Field(deprecated=True) warns on every read.
    user_api_identifier: str | None = Field(
        default=None,
        json_schema_extra={"deprecated": True},
    )


class Subscription(SubscriptionBase):
    """Schema representing a subscription in the system.

    Inherits endpoint and keys from SubscriptionBase and adds system fields.

    Attributes:
        endpoint (str): Push notification endpoint URL
        keys (dict[str, str | float | bool]): Dictionary containing encryption keys and auth info
        api_identifier (str): Unique API identifier for the subscription
    """

    model_config = ConfigDict(from_attributes=True)

    api_identifier: str
