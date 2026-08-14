"""Short link API endpoints.

Short links provide a compact ``/s/<token>`` URL that resolves to an existing
resource (currently letters, published or draft). Creating a link requires
READ permission on the target, so a link never grants access the creator did
not already have. Resolution requires authentication and returns only the
target identifier and type — never the underlying resource content — so a link
does not implicitly make a private resource public.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from ring.api_identifier.util import get_model
from ring.authz.authz import load_and_check
from ring.authz.enforcer import Action
from ring.fastapp.dependencies import (
    AuthenticatedRequestDependencies,
    get_request_dependencies,
)
from ring.links.constants import target_type_for_api_id
from ring.links.crud import short_link as short_link_crud
from ring.links.models.short_link_model import ShortLink
from ring.links.schemas.short_link import (
    ShortLink as ShortLinkSchema,
)
from ring.links.schemas.short_link import (
    ShortLinkCreate,
    ShortLinkResolution,
)

router = APIRouter()


@router.post(
    "/short-link",
    response_model=ShortLinkSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_short_link(
    payload: ShortLinkCreate,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> ShortLink:
    """Create (or reuse) a short link for a shareable resource.

    Args:
        payload (ShortLinkCreate): Target resource to share.
        req_dep (AuthenticatedRequestDependencies): Request dependencies.

    Returns:
        ShortLink: The new or pre-existing short link.

    Raises:
        HTTPException: 400 if the target type is not shareable; 404/permission
            errors surface from the authorization check.
    """
    if target_type_for_api_id(payload.target_api_id) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This resource type cannot be shared with a short link",
        )

    # READ permission on the target ensures a link never grants access the
    # creator did not already have.
    load_and_check(
        req_dep.db,
        req_dep.current_user,
        Action.READ,
        payload.target_api_id,
    )

    short_link = short_link_crud.create_short_link(
        req_dep.db,
        target_api_id=payload.target_api_id,
        creator=req_dep.current_user,
    )
    req_dep.db.commit()
    return short_link


@router.get(
    "/short-link/{token}",
    response_model=ShortLinkResolution,
)
async def resolve_short_link(
    token: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> ShortLinkResolution:
    """Resolve a short link token to its target resource.

    Returns only the target identifier and type; access to the underlying
    resource is still enforced by that resource's own endpoint.

    Args:
        token (str): The short link token.
        req_dep (AuthenticatedRequestDependencies): Request dependencies.

    Returns:
        ShortLinkResolution: The resolved target identifier and type.

    Raises:
        HTTPException: 404 if the token does not resolve to a shareable target.
    """
    short_link = short_link_crud.get_short_link_by_token(req_dep.db, token)
    target_type = (
        target_type_for_api_id(short_link.target_api_id)
        if short_link
        else None
    )
    if short_link is None or target_type is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short link not found",
        )

    return ShortLinkResolution(
        token=short_link.token,
        target_api_id=short_link.target_api_id,
        target_type=target_type,
    )


@router.delete(
    "/short-link/{short_link_api_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_short_link(
    short_link_api_id: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Response:
    """Revoke (hard-delete) a short link.

    Only the creator of the link may revoke it.

    Args:
        short_link_api_id (str): API identifier of the short link to revoke.
        req_dep (AuthenticatedRequestDependencies): Request dependencies.

    Returns:
        Response: An empty 204 response on success.

    Raises:
        HTTPException: 404 if the link is not found or not owned by the caller.
    """
    short_link = get_model(req_dep.db, ShortLink, short_link_api_id)
    if short_link.creator_id != req_dep.current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short link not found",
        )

    short_link_crud.delete_short_link(req_dep.db, short_link)
    req_dep.db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
