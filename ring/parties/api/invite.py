
from __future__ import annotations
from typing import Sequence
from fastapi import APIRouter, Depends
from ring.dependencies import (
    AuthenticatedRequestDependencies,
    RequestDependenciesBase,
    get_request_dependencies,
    get_unauthenticated_request_dependencies,
)
from fastapi import HTTPException
from ring.api_identifier import util as api_identifier_crud
from ring.parties.crud import invite as invite_crud
from ring.parties.models.invite_model import Invite
from ring.ring_pydantic import InviteLinked as InviteSchema
from ring.ring_pydantic.core import ResponseMessage
from ring.parties.schemas.invite import (
    InviteCreate,
)
from ring.ring_pydantic.linked_schemas import InviteLinked

router = APIRouter()


@router.post("/", response_model=InviteSchema)
async def create_invite(
    invite: InviteCreate,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Invite:
    existing_unexpired_invite = invite_crud.get_invite_by_email(req_dep.db, email=invite.email)
    if existing_unexpired_invite:
        raise HTTPException(status_code=400, detail="Email already invited")
    db_invite = invite_crud.create_invite(
        db=req_dep.db,
        email=invite.email,
        inviter_api_id=req_dep.current_user.api_identifier,
    )
    req_dep.db.commit()
    return db_invite

@router.get("/token/{token}", response_model=InviteLinked)
async def validate_token(
    token: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Invite:
    db_invite = invite_crud.get_invite_by_token(req_dep.db, token)
    if not db_invite:
        raise HTTPException(status_code=400, detail="Invalid token")
    if db_invite.is_expired:
        raise HTTPException(status_code=400, detail="Token expired")
    return db_invite
