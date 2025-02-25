from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from ring.api_identifier.util import get_model
from ring.dependencies import (
    AuthenticatedRequestDependencies,
    get_request_dependencies,
)
from ring.parties.crud.group_key_value import (
    delete_value,
    get_all_values,
    get_value,
    set_value,
)
from ring.parties.models.group_model import Group
from ring.parties.schemas.group_key_value import (
    BulkGroupKeyValueUpdate,
    GroupKeyValueBase,
    GroupKeyValueResponse,
    SingleGroupKeyValueUpdate,
)

router = APIRouter()


@router.get("/group/{group_api_id}/key-value")
async def read_group_key_values(
    group_api_id: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> GroupKeyValueResponse:
    db_group = get_model(req_dep.db, Group, api_id=group_api_id)
    if req_dep.current_user not in db_group.members:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Group not found",
        )
    return GroupKeyValueResponse(
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
    db_group = get_model(req_dep.db, Group, api_id=group_api_id)
    if req_dep.current_user not in db_group.members:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Group not found",
        )
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
    db_group = get_model(req_dep.db, Group, api_id=group_api_id)
    if req_dep.current_user not in db_group.members:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Group not found",
        )
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
) -> GroupKeyValueResponse:
    db_group = get_model(req_dep.db, Group, api_id=group_api_id)
    if req_dep.current_user not in db_group.members:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Group not found",
        )
    for update in updates.updates:
        if update.operation == "set":
            set_value(req_dep.db, db_group, update.key, update.value)
        elif update.operation == "delete":
            delete_value(req_dep.db, db_group, update.key)
    req_dep.db.commit()
    return GroupKeyValueResponse(
        key_values=get_all_values(req_dep.db, db_group)
    )
