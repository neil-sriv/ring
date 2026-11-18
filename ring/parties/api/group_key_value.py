from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Depends

from ring.authz.authz import load_and_check
from ring.authz.enforcer import Action
from ring.fastapp.dependencies import (
    AuthenticatedRequestDependencies,
    get_request_dependencies,
)
from ring.parties.crud.group_key_value import (
    delete_value,
    get_all_values,
    get_value,
    set_all_values,
    set_value,
)
from ring.parties.models.group_model import Group
from ring.parties.schemas.group_key_value import (
    BulkGroupKeyValueUpdate,
    GroupKeyValue,
    GroupKeyValueBase,
    SingleGroupKeyValueUpdate,
)

router = APIRouter()


def _load_group_for_member(
    req_dep: AuthenticatedRequestDependencies,
    group_api_id: str,
) -> Group:
    """Require group membership; missing groups look like forbidden access."""
    return cast(
        Group,
        load_and_check(
            req_dep.db,
            req_dep.current_user,
            Action.READ,
            group_api_id,
        ),
    )


@router.get("/group/{group_api_id}/key-value")
async def read_group_key_values(
    group_api_id: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> GroupKeyValue:
    """Get all key-value pairs for a group.

    Caller must be a member of the group. Missing groups look like forbidden
    access so callers cannot probe for ids.

    Args:
        group_api_id (str): API identifier of the group
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        GroupKeyValue: Dictionary of all key-value pairs

    Raises:
        PermissionError: If the group is missing or the caller cannot read it
    """
    db_group = _load_group_for_member(req_dep, group_api_id)
    return GroupKeyValue(
        key_values=get_all_values(req_dep.db, db_group),
    )


@router.get(
    "/group/{group_api_id}/key-value/{key}",
)
async def read_group_key_value(
    group_api_id: str,
    key: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> GroupKeyValueBase:
    """Get a specific key-value pair for a group.

    Caller must be a member of the group. Missing groups look like forbidden
    access so callers cannot probe for ids.

    Args:
        group_api_id (str): API identifier of the group
        key (str): Key to retrieve
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        GroupKeyValueBase: Key-value pair

    Raises:
        PermissionError: If the group is missing or the caller cannot read it
    """
    db_group = _load_group_for_member(req_dep, group_api_id)
    val = get_value(req_dep.db, db_group, key)
    return GroupKeyValueBase(key=key, value=val)


@router.post(
    "/group/{group_api_id}/key-value:update",
)
async def upsert_group_key_value(
    group_api_id: str,
    update: SingleGroupKeyValueUpdate,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> GroupKeyValueBase:
    """Update or delete a single key-value pair for a group.

    Caller must be a member of the group. Missing groups look like forbidden
    access so callers cannot probe for ids.

    Args:
        group_api_id (str): API identifier of the group
        update (SingleGroupKeyValueUpdate): Update operation details
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        GroupKeyValueBase: Updated key-value pair

    Raises:
        PermissionError: If the group is missing or the caller cannot read it
    """
    db_group = _load_group_for_member(req_dep, group_api_id)
    if update.operation == "set":
        set_value(req_dep.db, db_group, update.key, update.value)
    elif update.operation == "delete":
        delete_value(req_dep.db, db_group, update.key)
    req_dep.db.commit()
    return GroupKeyValueBase(
        key=update.key,
        value=get_value(req_dep.db, db_group, update.key),
    )


@router.post(
    "/group/{group_api_id}/key-value:bulk-update",
)
async def bulk_update_group_key_values(
    group_api_id: str,
    updates: BulkGroupKeyValueUpdate,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> GroupKeyValue:
    """Update or delete multiple key-value pairs for a group.

    Caller must be a member of the group. Missing groups look like forbidden
    access so callers cannot probe for ids.

    Args:
        group_api_id (str): API identifier of the group
        updates (BulkGroupKeyValueUpdate): List of update operations
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        GroupKeyValue: All key-value pairs after updates

    Raises:
        PermissionError: If the group is missing or the caller cannot read it
    """
    db_group = _load_group_for_member(req_dep, group_api_id)
    for update in updates.updates:
        if update.operation == "set":
            set_value(req_dep.db, db_group, update.key, update.value)
        elif update.operation == "delete":
            delete_value(req_dep.db, db_group, update.key)
    req_dep.db.commit()
    return GroupKeyValue(key_values=get_all_values(req_dep.db, db_group))


@router.put(
    "/group/{group_api_id}/key-value",
)
async def full_replace_group_key_values(
    group_api_id: str,
    updates: GroupKeyValue,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> GroupKeyValue:
    """Replace all key-value pairs for a group.

    Caller must be a member of the group. Missing groups look like forbidden
    access so callers cannot probe for ids.

    Args:
        group_api_id (str): API identifier of the group
        updates (GroupKeyValue): New key-value pairs
        req_dep (AuthenticatedRequestDependencies): Request dependencies

    Returns:
        GroupKeyValue: Updated key-value pairs

    Raises:
        PermissionError: If the group is missing or the caller cannot read it
    """
    db_group = _load_group_for_member(req_dep, group_api_id)
    set_all_values(req_dep.db, db_group, updates.key_values)
    req_dep.db.commit()
    return GroupKeyValue(key_values=get_all_values(req_dep.db, db_group))
