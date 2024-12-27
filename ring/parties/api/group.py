from __future__ import annotations

from datetime import timezone
from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, status

from ring.api_identifier import (
    util as api_identifier_crud,
)
from ring.dependencies import (
    AuthenticatedRequestDependencies,
    get_request_dependencies,
)
from ring.letters.crud.default_question import replace_default_questions
from ring.letters.crud.letter import add_participants
from ring.parties.crud import group as group_crud
from ring.parties.crud import invite as invite_crud
from ring.parties.models.group_model import Group
from ring.parties.models.user_model import User
from ring.parties.schemas.group import (
    AddMembers,
    GroupCreate,
    GroupUpdate,
    ReplaceDefaultQuestions,
)
from ring.ring_pydantic import GroupLinked as GroupSchema
from ring.tasks.schemas.schedule import ScheduleSendParam

router = APIRouter()


@router.post(
    "/group", response_model=GroupSchema, status_code=status.HTTP_201_CREATED
)
async def create_group(
    group: GroupCreate,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Group:
    db_group = group_crud.create_group(
        db=req_dep.db, admin_api_id=group.admin_api_identifier, name=group.name
    )
    req_dep.db.commit()
    return db_group


@router.get("/groups/", response_model=Sequence[GroupSchema])
async def list_groups(
    user_api_id: str,
    skip: int = 0,
    limit: int = 100,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Sequence[Group]:
    groups = group_crud.get_groups(
        req_dep.db,
        user_api_id=user_api_id,
        skip=skip,
        limit=limit,
    )
    return groups


@router.get("/group/{group_api_id}", response_model=GroupSchema)
async def read_group(
    group_api_id: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Group:
    db_group = api_identifier_crud.get_model(
        req_dep.db,
        Group,
        api_id=group_api_id,
    )
    if req_dep.current_user not in db_group.members:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Group not found",
        )
    return db_group


@router.post(
    "/group/{group_api_id}:add_member/{user_api_id}",
    response_model=GroupSchema,
)
async def add_user_to_group(
    group_api_id: str,
    user_api_id: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Group:
    group = group_crud.add_member(
        req_dep.db, group_api_id=group_api_id, user_api_id=user_api_id
    )
    req_dep.db.commit()
    return group


@router.post(
    "/group/{group_api_id}:remove_member/{user_api_id}",
    response_model=GroupSchema,
)
async def remove_user_from_group(
    group_api_id: str,
    user_api_id: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Group:
    db_group = api_identifier_crud.get_model(
        req_dep.db, Group, api_id=group_api_id
    )
    if req_dep.current_user not in db_group.members:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Group not found",
        )
    if req_dep.current_user != db_group.admin:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Only the group admin can remove members",
        )
    if user_api_id == req_dep.current_user.api_identifier:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Cannot remove yourself from the group",
        )
    db_user = api_identifier_crud.get_model(
        req_dep.db, User, api_id=user_api_id
    )
    if db_user not in db_group.members:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "User is not a member of the group",
        )
    group = group_crud.remove_member(
        req_dep.db, group_api_id=group_api_id, user_api_id=user_api_id
    )
    req_dep.db.commit()
    return group


@router.post(
    "/group/{group_api_id}:schedule_send",
    response_model=GroupSchema,
    deprecated=True,
)
async def schedule_send(
    group_api_id: str,
    schedule_param: ScheduleSendParam,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Group:
    utc_send_at = schedule_param.send_at.astimezone(tz=timezone.utc)
    group = group_crud.schedule_send(
        req_dep.db,
        group_api_id=group_api_id,
        letter_api_id=schedule_param.letter_api_id,
        send_at=utc_send_at,
    )
    req_dep.db.commit()
    return group


@router.patch(
    "/group/{group_api_id}",
    response_model=GroupSchema,
)
def update_group(
    group_api_id: str,
    group: GroupUpdate,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Group:
    if not group.name:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No name provided")
    db_group = api_identifier_crud.get_model(
        req_dep.db, Group, api_id=group_api_id
    )
    if req_dep.current_user != db_group.admin:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Only the group admin can update the group information",
        )
    db_group.name = group.name
    req_dep.db.commit()
    return db_group


@router.post(
    "/group/{group_api_id}:add_members",
    response_model=GroupSchema,
)
def add_members(
    group_api_id: str,
    add_members: AddMembers,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Group:
    db_group = api_identifier_crud.get_model(
        req_dep.db, Group, api_id=group_api_id
    )
    if not add_members.member_emails:
        return db_group
    db_users = (
        req_dep.db.query(User)
        .where(User.email.in_(add_members.member_emails))
        .all()
    )
    unregistered = [
        email
        for email in add_members.member_emails
        if email not in [db_u.email for db_u in db_users]
    ]
    invites = invite_crud.invite_users(
        req_dep.db, db_group, req_dep.current_user, unregistered
    )
    group_crud.add_members(req_dep.db, db_group, db_users)
    in_prog, upcoming = db_group.in_progress_letter, db_group.upcoming_letter
    if in_prog is not None:
        add_participants(req_dep.db, in_prog, db_users)
    if upcoming is not None:
        add_participants(req_dep.db, upcoming, db_users)
    req_dep.db.commit()

    if invites:
        [
            invite_crud.email_user_invites.delay([invite.id])
            for invite in invites
        ]

    return db_group


@router.post(
    "/group/{group_api_id}:replace_default_questions",
    response_model=GroupSchema,
)
def replace_group_default_questions(
    group_api_id: str,
    default_questions: ReplaceDefaultQuestions,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Group:
    db_group = api_identifier_crud.get_model(
        req_dep.db, Group, api_id=group_api_id
    )
    if req_dep.current_user != db_group.admin:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Only the group admin can replace default questions",
        )
    replace_default_questions(
        req_dep.db, db_group, default_questions.questions
    )
    req_dep.db.commit()
    return db_group
