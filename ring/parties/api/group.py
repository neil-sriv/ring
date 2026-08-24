from __future__ import annotations

from datetime import timezone
from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, status

from ring.api_identifier import (
    util as api_identifier_crud,
)
from ring.async_scheduler.scheduler import scheduler
from ring.fastapp.dependencies import (
    AuthenticatedRequestDependencies,
    get_request_dependencies,
)
from ring.letters.crud.default_question import replace_default_questions
from ring.notifications.crud.events import notify_added_to_group
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
    """Create a new group.

    Args:
        group (GroupCreate): Group creation parameters
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        Group: Created group

    Raises:
        HTTPException: If group creation fails
    """
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
    """List all groups a user is a member of.

    Args:
        user_api_id (str): API identifier of the user
        skip (int, optional): Number of records to skip. Defaults to 0.
        limit (int, optional): Maximum number of records to return. Defaults to 100.
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        Sequence[Group]: List of groups
    """
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
    """Get details of a specific group.

    Args:
        group_api_id (str): API identifier of the group
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        Group: Group details

    Raises:
        HTTPException: If group not found or user is not a member
    """
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
    """Add a user to a group.

    Args:
        group_api_id (str): API identifier of the group
        user_api_id (str): API identifier of the user to add
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        Group: Updated group

    Raises:
        HTTPException: If group or user not found
    """
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
    """Remove a user from a group.

    Args:
        group_api_id (str): API identifier of the group
        user_api_id (str): API identifier of the user to remove
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        Group: Updated group

    Raises:
        HTTPException: If group not found, user not authorized, or invalid operation
    """
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


@router.patch(
    "/group/{group_api_id}",
    response_model=GroupSchema,
)
async def update_group(
    group_api_id: str,
    group: GroupUpdate,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Group:
    """Update group information.

    Args:
        group_api_id (str): API identifier of the group
        group (GroupUpdate): Group update parameters
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        Group: Updated group

    Raises:
        HTTPException: If no updates provided, user not authorized, or invalid cycle length
    """
    if (
        not group.name
        and group.cycle_length is None
        and group.min_responder_ratio is None
        and "min_responder_ratio" not in group.model_fields_set
    ):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No updates provided")
    db_group = api_identifier_crud.get_model(
        req_dep.db, Group, api_id=group_api_id
    )
    if req_dep.current_user != db_group.admin:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Only the group admin can update the group information",
        )
    if group.name:
        db_group.name = group.name
    if group.cycle_length is not None:
        if group.cycle_length <= 0:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Cycle length must be greater than 0",
            )
        group_crud.update_cycle_length(
            req_dep.db, db_group, group.cycle_length
        )
    if "min_responder_ratio" in group.model_fields_set:
        try:
            group_crud.update_min_responder_ratio(
                req_dep.db, db_group, group.min_responder_ratio
            )
        except ValueError as exc:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                str(exc),
            ) from exc
    req_dep.db.commit()
    return db_group


@router.post(
    "/group/{group_api_id}:add_members",
    response_model=GroupSchema,
)
async def add_members(
    group_api_id: str,
    add_members: AddMembers,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Group:
    """Add multiple members to a group.

    Args:
        group_api_id (str): API identifier of the group
        add_members (AddMembers): List of email addresses to invite
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        Group: Updated group

    Note:
        - Existing users will be added directly to the group
        - Non-registered users will receive email invitations
        - New members are automatically added to in-progress and upcoming letters
    """
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
    added_members = group_crud.add_members(req_dep.db, db_group, db_users)
    notify_added_to_group(
        req_dep.db, db_group, added_members, req_dep.current_user
    )
    req_dep.db.commit()

    if invites:
        scheduler.add_job(
            invite_crud.email_user_invites,
            args=[[invite.id for invite in invites]],
        )
    return db_group


@router.post(
    "/group/{group_api_id}:replace_default_questions",
    response_model=GroupSchema,
)
async def replace_group_default_questions(
    group_api_id: str,
    default_questions: ReplaceDefaultQuestions,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Group:
    """Replace a group's default questions.

    Args:
        group_api_id (str): API identifier of the group
        default_questions (ReplaceDefaultQuestions): New list of default questions
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        Group: Updated group

    Raises:
        HTTPException: If group not found or user not authorized
    """
    db_group = api_identifier_crud.get_model(
        req_dep.db, Group, api_id=group_api_id
    )
    if req_dep.current_user != db_group.admin:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Only the group admin can update the default questions",
        )
    replace_default_questions(
        req_dep.db, db_group, default_questions.questions
    )
    req_dep.db.commit()
    return db_group
