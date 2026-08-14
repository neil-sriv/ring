"""Authenticated endpoints for minting and revoking share links.

Only a member who can read a resource may mint or revoke its share link: a
share link exposes a strict subset of what that member can already see, so the
permission to create one is the permission to read the target.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ring.authz.authz import load_and_check
from ring.authz.enforcer import Action
from ring.fastapp.dependencies import (
    AuthenticatedRequestDependencies,
    get_request_dependencies,
)
from ring.lib.app_links import app_url
from ring.sharing.crud import share_link as share_link_crud
from ring.sharing.models.share_link_model import ShareLink
from ring.sharing.schemas.share_link import (
    ShareLinkCreate,
    ShareLinkResponse,
)

router = APIRouter()


def _share_url(target_api_id: str, token: str) -> str:
    """Build the absolute URL a person shares, carrying the token.

    Args:
        target_api_id (str): API id of the shared resource
        token (str): The capability token

    Returns:
        str: Absolute URL like `https://.../loops/lttr_x?s=sh_...`

    Raises:
        HTTPException: 422 if the resource type cannot be shared
    """
    path = share_link_crud.app_path_for_target(target_api_id)
    if path is None:
        raise HTTPException(
            status_code=422,
            detail=f"Resource {target_api_id} cannot be shared",
        )
    return app_url(f"{path}?s={token}")


def _authorize_target(
    db: Session,
    req_dep: AuthenticatedRequestDependencies,
    target_api_id: str,
) -> None:
    """Require that the current user can read the target resource.

    `load_and_check` raises `PermissionError` both when the user lacks access
    and when the resource does not exist; either way the caller learns nothing
    it should not, so both map to 403.
    """
    try:
        load_and_check(db, req_dep.current_user, Action.READ, target_api_id)
    except PermissionError:
        raise HTTPException(
            status_code=403,
            detail="Not allowed to share this resource",
        )


def _to_response(share_link: ShareLink) -> ShareLinkResponse:
    return ShareLinkResponse(
        api_identifier=share_link.api_identifier,
        token=share_link.token,
        target_api_id=share_link.target_api_id,
        share_url=_share_url(share_link.target_api_id, share_link.token),
        created_at=share_link.created_at,
    )


@router.post("/", response_model=ShareLinkResponse)
async def create_share_link(
    payload: ShareLinkCreate,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> ShareLinkResponse:
    """Mint (or return the existing) share link for a resource."""
    _authorize_target(req_dep.db, req_dep, payload.target_api_id)
    # Reject unshareable types before minting a token that could never resolve.
    _share_url(payload.target_api_id, "")
    share_link = share_link_crud.get_or_create_share_link(
        req_dep.db,
        target_api_id=payload.target_api_id,
        created_by_api_id=req_dep.current_user.api_identifier,
    )
    req_dep.db.commit()
    req_dep.db.refresh(share_link)
    return _to_response(share_link)


@router.get("/", response_model=ShareLinkResponse)
async def get_share_link(
    target_api_id: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> ShareLinkResponse:
    """Return the existing share link for a resource, if any."""
    _authorize_target(req_dep.db, req_dep, target_api_id)
    share_link = share_link_crud.get_share_link_for_target(
        req_dep.db, target_api_id
    )
    if share_link is None:
        raise HTTPException(status_code=404, detail="No share link")
    return _to_response(share_link)


@router.delete(
    "/{token}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def revoke_share_link(
    token: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> None:
    """Revoke a share link, so its URL stops enriching previews."""
    share_link = share_link_crud.get_share_link_by_token(req_dep.db, token)
    if share_link is None:
        raise HTTPException(status_code=404, detail="No share link")
    _authorize_target(req_dep.db, req_dep, share_link.target_api_id)
    share_link_crud.revoke_share_link(req_dep.db, share_link)
    req_dep.db.commit()
    return None
