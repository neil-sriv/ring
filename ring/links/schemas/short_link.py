"""Pydantic schemas for short links.

Short links are compact, shareable tokens that resolve to an existing
API-identified resource (currently letters, published or draft). They provide a
tidy ``/s/<token>`` URL for sharing without exposing the longer
``api_identifier`` or leaking additional data.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from ring.links.constants import ShortLinkTargetType


class ShortLinkCreate(BaseModel):
    """Schema for creating (or reusing) a short link.

    Attributes:
        target_api_id (str): API identifier of the resource to share. Must be a
            supported target type (see ``ShortLinkTargetType``).
    """

    target_api_id: str


class ShortLink(BaseModel):
    """Schema representing a short link in the system.

    Attributes:
        api_identifier (str): Unique API identifier for the short link.
        token (str): The short, URL-safe token used in the shareable path.
        target_api_id (str): API identifier of the resource the link resolves to.
        target_type (ShortLinkTargetType): Category of the resolved resource.
        path (str): Relative shareable path, e.g. ``/s/<token>``.
    """

    model_config = ConfigDict(from_attributes=True)

    api_identifier: str
    token: str
    target_api_id: str
    target_type: ShortLinkTargetType
    path: str


class ShortLinkResolution(BaseModel):
    """Schema returned when resolving a token to its target.

    Attributes:
        token (str): The resolved token.
        target_api_id (str): API identifier of the resource to redirect to.
        target_type (ShortLinkTargetType): Category of the resolved resource.
    """

    token: str
    target_api_id: str
    target_type: ShortLinkTargetType
