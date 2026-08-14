"""Pydantic schemas for share links."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ShareLinkCreate(BaseModel):
    """Request to mint (or fetch) a share link for a resource.

    Attributes:
        target_api_id (str): API id of the resource to share (e.g. a letter)
    """

    target_api_id: str


class ShareLinkResponse(BaseModel):
    """A share link and the URL to hand out.

    Attributes:
        api_identifier (str): The share link's own API id
        token (str): The capability token embedded in the URL
        target_api_id (str): API id of the shared resource
        share_url (str): Absolute URL to share, carrying the token
        created_at (datetime): When the link was minted
    """

    api_identifier: str
    token: str
    target_api_id: str
    share_url: str
    created_at: datetime
