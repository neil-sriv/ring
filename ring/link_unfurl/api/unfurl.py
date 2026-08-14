"""API endpoints for link unfurling (rich URL previews).

Exposes a single authenticated endpoint that fetches a URL server-side and
returns Open Graph-style metadata for rendering a preview card. Requiring
authentication keeps the fetcher from becoming an open SSRF proxy.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from ring.fastapp.dependencies import (
    AuthenticatedRequestDependencies,
    get_request_dependencies,
)
from ring.link_unfurl.schemas.link_preview import (
    LinkPreview,
    LinkPreviewRequest,
)
from ring.link_unfurl.service import (
    LinkUnfurlError,
    UnsafeURLError,
    unfurl_url,
)

router = APIRouter()


@router.post("/unfurl", response_model=LinkPreview)
async def unfurl_link(
    request: LinkPreviewRequest,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> LinkPreview:
    """Fetch a URL and return a rich preview of its page metadata.

    Args:
        request (LinkPreviewRequest): The URL to unfurl.
        req_dep (AuthenticatedRequestDependencies): Request dependencies;
            authentication is required so the endpoint is not an open proxy.

    Returns:
        LinkPreview: The preview metadata for the URL.

    Raises:
        HTTPException: 400 if the URL is invalid or unsafe to fetch, 502 if
            the URL could not be fetched or parsed.
    """
    try:
        return await unfurl_url(request.url)
    except UnsafeURLError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except LinkUnfurlError as exc:
        logger.info(f"Could not unfurl link: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not fetch link preview",
        ) from exc
