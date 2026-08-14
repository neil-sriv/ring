"""Crawler-facing HTML so shared links preview in chat apps."""

from __future__ import annotations

import html

from fastapi import APIRouter, Response

from ring.lib.app_links import app_url
from ring.unfurl.cards import (
    OG_IMAGE_ALT,
    OG_IMAGE_HEIGHT,
    OG_IMAGE_PATH,
    OG_IMAGE_WIDTH,
    SITE_NAME,
    card_for_path,
)

router = APIRouter()


def render_unfurl_html(path: str) -> str:
    """Render the head-only HTML a link-preview crawler reads.

    Slack fetches only the first 32KB of the response (with a `Range` header),
    so every tag stays at the top of `<head>`.

    Args:
        path (str): Path within the web app the shared link pointed at

    Returns:
        str: Complete HTML document carrying the Open Graph and Twitter tags
    """
    card = card_for_path(path)
    title = html.escape(card.title)
    description = html.escape(card.description)
    # The path comes off the request line, so it is escaped before it reaches
    # an attribute.
    canonical_url = html.escape(app_url(path))
    image_url = html.escape(app_url(OG_IMAGE_PATH))

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>{title}</title>
    <meta name="description" content="{description}" />
    <link rel="canonical" href="{canonical_url}" />
    <meta property="og:site_name" content="{SITE_NAME}" />
    <meta property="og:type" content="website" />
    <meta property="og:title" content="{title}" />
    <meta property="og:description" content="{description}" />
    <meta property="og:url" content="{canonical_url}" />
    <meta property="og:image" content="{image_url}" />
    <meta property="og:image:width" content="{OG_IMAGE_WIDTH}" />
    <meta property="og:image:height" content="{OG_IMAGE_HEIGHT}" />
    <meta property="og:image:alt" content="{OG_IMAGE_ALT}" />
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="{title}" />
    <meta name="twitter:description" content="{description}" />
    <meta name="twitter:image" content="{image_url}" />
    <meta name="theme-color" content="#051a3b" />
    <link rel="icon" href="/assets/images/favicon.ico" />
    <link rel="apple-touch-icon" href="/assets/images/apple-touch-icon-180x180.png" />
  </head>
  <body>
    <p>{description}</p>
    <p><a href="{canonical_url}">{canonical_url}</a></p>
  </body>
</html>
"""


# Some crawlers probe with HEAD before fetching; a 405 there is enough for them
# to give up on the link.
@router.api_route(
    "/unfurl/{app_path:path}",
    methods=["GET", "HEAD"],
    include_in_schema=False,
)
def unfurl(app_path: str) -> Response:
    """Serve link-preview HTML for a path in the web app.

    Nginx sends only link-preview crawlers here (see the `ring_link_bot` map in
    `prod.nginx.conf`); browsers keep getting the real single-page app. Kept
    out of the OpenAPI schema because no frontend code calls it, so it does not
    churn the generated client.

    Args:
        app_path (str): Path within the web app, as forwarded by nginx

    Returns:
        Response: HTML document carrying the preview tags
    """
    return Response(
        content=render_unfurl_html(app_path),
        media_type="text/html; charset=utf-8",
        headers={
            # Cloudflare ignores Vary, so a public cache on the page URL can
            # hand this head-only card to a browser and replace the SPA.
            # Slack/Discord cache on their side; we must not.
            "Cache-Control": "private, no-store",
        },
    )
