"""Pydantic schemas for link unfurling (rich URL previews).

These schemas model the request to unfurl a URL and the resulting Open
Graph-style preview returned to the frontend.
"""

from __future__ import annotations

from pydantic import BaseModel


class LinkPreviewRequest(BaseModel):
    """Request body for unfurling a single URL.

    Attributes:
        url (str): The URL to fetch and unfurl. Must be an http(s) URL.
    """

    url: str


class LinkPreview(BaseModel):
    """A rich preview of a URL built from its page metadata.

    All descriptive fields are optional because a page may only expose a
    subset of Open Graph / Twitter card / standard meta tags.

    Attributes:
        url (str): The URL that was requested.
        resolved_url (str): The final URL after following redirects.
        title (str | None): Best-effort page title.
        description (str | None): Best-effort page description.
        image_url (str | None): Absolute URL of the preview image.
        site_name (str | None): Human-readable site name.
        favicon_url (str | None): Absolute URL of the site favicon.
    """

    url: str
    resolved_url: str
    title: str | None = None
    description: str | None = None
    image_url: str | None = None
    site_name: str | None = None
    favicon_url: str | None = None
