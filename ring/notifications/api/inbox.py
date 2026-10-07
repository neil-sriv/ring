"""In-app inbox routes: list, unread count, and mark read."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ring.authz.authz import load_and_check
from ring.authz.enforcer import Action
from ring.fastapp.dependencies import (
    AuthenticatedRequestDependencies,
    get_request_dependencies,
)
from ring.notifications.crud.inbox import (
    list_inbox_items,
    mark_all_inbox_read,
    mark_inbox_read,
    unread_count,
)
from ring.notifications.models.inbox_item import InboxItem
from ring.notifications.schemas.inbox import (
    InboxItemResponse,
    InboxUnreadCount,
)
from ring.ring_pydantic.core import ResponseMessage

router = APIRouter()


@router.get("/inbox", response_model=list[InboxItemResponse])
def list_inbox(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    unread_only: bool = False,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> list[InboxItem]:
    """List the current user's inbox, newest first.

    Rows are selected by recipient. Other users' items are not loaded.
    """
    return list_inbox_items(
        req_dep.db,
        req_dep.current_user,
        skip=skip,
        limit=limit,
        unread_only=unread_only,
    )


@router.get("/inbox/unread-count", response_model=InboxUnreadCount)
def get_unread_count(
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> InboxUnreadCount:
    """Return how many of the current user's inbox rows are unread."""
    return InboxUnreadCount(
        unread_count=unread_count(req_dep.db, req_dep.current_user)
    )


@router.post("/inbox/read-all", response_model=ResponseMessage)
def read_all_inbox(
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> ResponseMessage:
    """Mark every unread inbox row for the current user as read."""
    updated = mark_all_inbox_read(req_dep.db, req_dep.current_user)
    req_dep.db.commit()
    return ResponseMessage(message=f"Marked {updated} inbox items read")


@router.post(
    "/inbox/{inbox_api_id}/read",
    response_model=InboxItemResponse,
)
def read_inbox_item(
    inbox_api_id: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> InboxItem:
    """Mark one inbox item read.

    Authorization uses the scoped enforcer for this id. A missing id and
    another user's id both return 403.
    """
    item = load_and_check(
        req_dep.db,
        req_dep.current_user,
        Action.WRITE,
        inbox_api_id,
    )
    assert isinstance(item, InboxItem)
    mark_inbox_read(item)
    req_dep.db.commit()
    return item
