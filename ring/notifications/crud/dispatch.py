"""Persist an inbox row per recipient and web-push after commit.

Inbox rows are written in the caller's transaction. Web pushes are queued
on that session and sent from its after-commit hook, so a rollback never
pushes. Push failures are logged and never raised.
"""

from __future__ import annotations

from typing import NamedTuple, Sequence

from loguru import logger
from sqlalchemy import event
from sqlalchemy.orm import Session, SessionTransaction

from ring.lib.app_links import app_url
from ring.notifications.crud.inbox import create_inbox_item
from ring.notifications.crud.links import inbox_href
from ring.notifications.crud.subscription import serialize_subscription_info
from ring.notifications.crud.vapid import send_push_notification
from ring.notifications.models.inbox_item import InboxItem
from ring.parties.models.user_model import User

_PENDING_PUSHES = "ring.notifications.pending_web_pushes"


class _PendingPush(NamedTuple):
    subscription_info: dict[str, str]
    payload: dict[str, str]
    user_api_identifier: str


def notify_users(
    db: Session,
    users: Sequence[User],
    *,
    title: str,
    body: str,
    target_api_id: str | None,
) -> list[InboxItem]:
    """Create one inbox row per recipient and queue a web push.

    Recipients are de-duplicated by id. A user with no push subscription
    still gets an inbox row. The caller commits. Pushes are sent after
    that commit and dropped on rollback.
    """
    seen: set[int] = set()
    created: list[InboxItem] = []
    for user in users:
        if user.id in seen:
            continue
        seen.add(user.id)
        item = create_inbox_item(
            db,
            user,
            title=title,
            body=body,
            target_api_id=target_api_id,
        )
        created.append(item)
        _queue_web_push(db, user, title, body, target_api_id)
    return created


def _queue_web_push(
    db: Session,
    user: User,
    title: str,
    body: str,
    target_api_id: str | None,
) -> None:
    subscriptions = user.notification_subscriptions
    if not subscriptions:
        return
    pending: list[_PendingPush] = db.info.setdefault(_PENDING_PUSHES, [])
    pending.append(
        _PendingPush(
            subscription_info=serialize_subscription_info(subscriptions[-1]),
            payload={
                "title": title,
                "body": body,
                "url": app_url(inbox_href(target_api_id).lstrip("/")),
            },
            user_api_identifier=user.api_identifier,
        )
    )


def _deliver_pending_pushes(session: Session) -> None:
    if session.in_nested_transaction():
        return
    pending: list[_PendingPush] | None = session.info.pop(
        _PENDING_PUSHES, None
    )
    if not pending:
        return
    for push in pending:
        try:
            send_push_notification(push.subscription_info, push.payload)
        except Exception:
            logger.exception(
                "Web push failed for user {}",
                push.user_api_identifier,
            )


def _discard_pending_pushes(session: Session) -> None:
    if session.in_nested_transaction():
        return
    session.info.pop(_PENDING_PUSHES, None)


def _discard_pending_pushes_on_close(
    session: Session, transaction: SessionTransaction
) -> None:
    if transaction.nested or transaction.parent is not None:
        return
    session.info.pop(_PENDING_PUSHES, None)


event.listen(Session, "after_commit", _deliver_pending_pushes)
event.listen(Session, "after_rollback", _discard_pending_pushes)
event.listen(
    Session, "after_transaction_end", _discard_pending_pushes_on_close
)
