"""Persist an inbox row for each web-push send, then push.

The existing VAPID helper delivers the browser notification. It does not
write a row. ``notify_users`` records the send first, then calls that helper.
Push failures are logged and never raised, so email and membership flows
still commit.
"""

from __future__ import annotations

from typing import Sequence

from loguru import logger
from sqlalchemy.orm import Session

from ring.lib.app_links import app_url
from ring.notifications.crud.inbox import create_inbox_item
from ring.notifications.crud.links import inbox_href
from ring.notifications.crud.vapid import send_push_notification
from ring.notifications.models.inbox_item import InboxItem
from ring.parties.models.user_model import User


def notify_users(
    db: Session,
    users: Sequence[User],
    *,
    title: str,
    body: str,
    target_api_id: str | None,
) -> list[InboxItem]:
    """Create one inbox row per recipient and best-effort web-push it.

    Recipients are de-duplicated by id. A user with no push subscription
    still gets an inbox row. The caller commits.
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
        _push_best_effort(user, title, body, target_api_id)
    return created


def _push_best_effort(
    user: User,
    title: str,
    body: str,
    target_api_id: str | None,
) -> None:
    subscriptions = user.notification_subscriptions
    if not subscriptions:
        return
    payload = {
        "title": title,
        "body": body,
        "url": app_url(inbox_href(target_api_id).lstrip("/")),
    }
    try:
        send_push_notification(subscriptions[-1], payload)
    except Exception:
        logger.exception(
            "Web push failed for user {}",
            user.api_identifier,
        )
