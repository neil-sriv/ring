from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Depends, HTTPException, status

from ring.api_identifier import util as api_identifier_crud
from ring.authz.authz import load_and_check
from ring.authz.enforcer import Action
from ring.fastapp.dependencies import (
    AuthenticatedRequestDependencies,
    RequestDependenciesBase,
    get_request_dependencies,
    get_unauthenticated_request_dependencies,
)
from ring.parties.crud import invite as invite_crud
from ring.parties.crud.one_time_token import (
    TokenAlreadyUsedError,
    TokenExpiredError,
)
from ring.parties.crud.user import get_user_by_email
from ring.parties.models.group_model import Group
from ring.parties.models.invite_model import Invite
from ring.parties.models.user_model import User
from ring.parties.schemas.invite import (
    InviteCreate,
)
from ring.ring_pydantic import InviteLinked as InviteSchema
from ring.ring_pydantic.linked_schemas import InviteLinked

router = APIRouter()


def _require_group_admin(user: User, group: Group) -> None:
    """Match add_members: only the group admin may create invites."""
    if user != group.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the group admin can create invites",
        )


@router.post("/", response_model=InviteSchema)
async def create_invite(
    invite: InviteCreate,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Invite:
    """Create a new invite for a user to join a group.

    Only the group admin may create invites. Callers who are not members of
    the group receive a generic 403 so resource existence cannot be probed.

    Args:
        invite (InviteCreate): Invite creation parameters including email and group_api_id
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        Invite: Created invite

    Raises:
        HTTPException: If email is already invited/registered, or caller is not admin
        PermissionError: If the group is missing or the caller cannot read it
    """
    db_group = cast(
        Group,
        load_and_check(
            req_dep.db,
            req_dep.current_user,
            Action.READ,
            invite.group_api_id,
        ),
    )
    _require_group_admin(req_dep.current_user, db_group)

    existing_unexpired_invite = invite_crud.get_invite_by_email(
        req_dep.db, email=invite.email
    )
    if existing_unexpired_invite:
        raise HTTPException(status_code=400, detail="Email already invited")
    existing_user = get_user_by_email(req_dep.db, email=invite.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_inviter = api_identifier_crud.get_model(
        req_dep.db, User, api_id=req_dep.current_user.api_identifier
    )

    [db_invite] = invite_crud.invite_users(
        db=req_dep.db,
        emails=[invite.email],
        inviter=db_inviter,
        group=db_group,
    )
    req_dep.db.commit()
    return db_invite


@router.get("/token/{token}", response_model=InviteLinked)
async def validate_token(
    token: str,
    req_dep: RequestDependenciesBase = Depends(
        get_unauthenticated_request_dependencies,
    ),
) -> Invite:
    """Validate an invite token and return the associated invite.

    Args:
        token (str): The invite token to validate
        req_dep (RequestDependenciesBase): Request dependencies

    Returns:
        Invite: The invite associated with the token

    Raises:
        HTTPException: If token is invalid, expired, or already used
    """
    try:
        db_invite = invite_crud.get_invite_by_token(req_dep.db, token)
    except (TokenAlreadyUsedError, TokenExpiredError):
        raise HTTPException(status_code=400, detail="Invalid token")
    if not db_invite:
        raise HTTPException(status_code=400, detail="Invalid token")
    return db_invite
