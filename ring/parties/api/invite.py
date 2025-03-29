from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ring.api_identifier import util as api_identifier_crud
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


@router.post("/", response_model=InviteSchema)
async def create_invite(
    invite: InviteCreate,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Invite:
    """Create a new invite for a user to join a group.

    Args:
        invite (InviteCreate): Invite creation parameters including email and group_api_id
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        Invite: Created invite

    Raises:
        HTTPException: If email is already invited, already registered, or group not found
    """
    existing_unexpired_invite = invite_crud.get_invite_by_email(
        req_dep.db, email=invite.email
    )
    if existing_unexpired_invite:
        raise HTTPException(status_code=400, detail="Email already invited")
    existing_user = get_user_by_email(req_dep.db, email=invite.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_group = api_identifier_crud.get_model(
        req_dep.db, Group, api_id=invite.group_api_id
    )
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
