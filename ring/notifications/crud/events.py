"""Product-event notification helpers.

Each helper knows which users a product event should notify and what the
in-app / push copy looks like, then hands off to
:func:`ring.notifications.crud.dispatch.notify_users`. These mirror the
transactional emails so users who live in the app (or rely on web push) see
the same high-value moments: a letter going out, response windows opening
and closing, a letter waiting on them, and being added to a group.

Callers are responsible for committing the session, matching the CRUD
convention across domains.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from ring.letters.constants import LetterStatus
from ring.notifications.constants import NotificationType
from ring.notifications.crud.dispatch import notify_users
from ring.tasks.crud.waiting_response_email_task import (
    letter_display_title,
    letter_non_responder_users,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from ring.letters.models.letter_model import Letter
    from ring.notifications.models.notification import Notification
    from ring.parties.models.group_model import Group
    from ring.parties.models.user_model import User


def notify_letter_sent(db: Session, letter: Letter) -> list[Notification]:
    """Notify all participants that a letter was published.

    Mirrors the letter send email.

    Args:
        db (Session): Database session
        letter (Letter): The letter that was just sent

    Returns:
        list[Notification]: Created in-app notifications
    """
    return notify_users(
        db,
        letter.participants,
        type=NotificationType.LETTER_SENT,
        title=f"New letter from {letter.group.name}",
        body=f"{letter_display_title(letter)} is ready to read.",
        target_api_id=letter.api_identifier,
    )


def notify_responses_open(db: Session, letter: Letter) -> list[Notification]:
    """Notify all participants that a letter is open for responses.

    Mirrors the response-open email sent when a letter is promoted from
    UPCOMING to IN_PROGRESS.

    Args:
        db (Session): Database session
        letter (Letter): The letter that just opened for responses

    Returns:
        list[Notification]: Created in-app notifications
    """
    return notify_users(
        db,
        letter.participants,
        type=NotificationType.RESPONSES_OPEN,
        title=f"{letter.group.name} is open for responses",
        body=(f"{letter_display_title(letter)} is ready for your answers."),
        target_api_id=letter.api_identifier,
    )


def notify_letter_reminder(db: Session, letter: Letter) -> list[Notification]:
    """Remind all participants about a letter deadline.

    Mirrors the reminder email: upcoming letters remind about adding
    questions, in-progress letters about responding.

    Args:
        db (Session): Database session
        letter (Letter): The letter the reminder is for

    Returns:
        list[Notification]: Created in-app notifications
    """
    action = (
        "add questions"
        if letter.status == LetterStatus.UPCOMING
        else "respond"
    )
    return notify_users(
        db,
        letter.participants,
        type=NotificationType.LETTER_REMINDER,
        title=f"Last day to {action} for {letter.group.name}",
        body=(
            f"{letter_display_title(letter)} closes today — "
            f"{action} before it goes out."
        ),
        target_api_id=letter.api_identifier,
    )


def notify_awaiting_response(
    db: Session, letter: Letter
) -> list[Notification]:
    """Notify non-responders that a deferred letter is waiting on them.

    Mirrors the waiting-response email sent when a letter send is deferred
    below the responder threshold. No-ops when everyone has answered.

    Args:
        db (Session): Database session
        letter (Letter): The deferred letter

    Returns:
        list[Notification]: Created in-app notifications
    """
    non_responders = letter_non_responder_users(letter)
    if not non_responders:
        return []
    return notify_users(
        db,
        non_responders,
        type=NotificationType.AWAITING_RESPONSE,
        title=f"{letter_display_title(letter)} is waiting on you",
        body=(
            f"{letter.group.name}'s latest letter can't go out until "
            "you respond."
        ),
        target_api_id=letter.api_identifier,
    )


def notify_added_to_group(
    db: Session,
    group: Group,
    added_users: Sequence[User],
    added_by: User,
) -> list[Notification]:
    """Notify users that they were added to a group.

    Registered users added via the add-members flow get an in-app
    notification (unregistered emails get the invite email instead).

    Args:
        db (Session): Database session
        group (Group): Group the users were added to
        added_users (Sequence[User]): Users who were just added
        added_by (User): User who performed the add

    Returns:
        list[Notification]: Created in-app notifications
    """
    recipients = [user for user in added_users if user.id != added_by.id]
    if not recipients:
        return []
    actor = added_by.name or added_by.email
    return notify_users(
        db,
        recipients,
        type=NotificationType.ADDED_TO_GROUP,
        title=f"You've been added to {group.name}",
        body=f"{actor} added you to the loop.",
        target_api_id=group.api_identifier,
    )
