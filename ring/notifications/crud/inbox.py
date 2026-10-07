"""CRUD for in-app inbox items."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ring.notifications.models.inbox_item import InboxItem
from ring.parties.models.user_model import User


def create_inbox_item(
    db: Session,
    user: User,
    title: str,
    body: str,
    target_api_id: str | None,
) -> InboxItem:
    """Insert one unread inbox row. The caller commits."""
    item = InboxItem.create(
        user=user,
        title=title,
        body=body,
        target_api_id=target_api_id,
    )
    db.add(item)
    return item


def list_inbox_items(
    db: Session,
    user: User,
    *,
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
) -> list[InboxItem]:
    """List the user's inbox, newest first."""
    stmt = select(InboxItem).where(InboxItem.user_id == user.id)
    if unread_only:
        stmt = stmt.where(InboxItem.read_at.is_(None))
    stmt = (
        stmt.order_by(InboxItem.created_at.desc(), InboxItem.id.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def unread_count(db: Session, user: User) -> int:
    """Count inbox rows the user has not marked read."""
    count = db.scalar(
        select(func.count())
        .select_from(InboxItem)
        .where(
            InboxItem.user_id == user.id,
            InboxItem.read_at.is_(None),
        )
    )
    return int(count or 0)


def mark_inbox_read(item: InboxItem) -> InboxItem:
    """Mark one item read. A second call leaves the original timestamp."""
    if item.read_at is None:
        item.read_at = datetime.now(UTC)
    return item


def mark_all_inbox_read(db: Session, user: User) -> int:
    """Mark every unread row for this user read. Returns how many changed."""
    items = list(
        db.scalars(
            select(InboxItem).where(
                InboxItem.user_id == user.id,
                InboxItem.read_at.is_(None),
            )
        ).all()
    )
    now = datetime.now(UTC)
    for item in items:
        item.read_at = now
    return len(items)
