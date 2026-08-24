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
    from ring.letters.models.question_model import Question
    from ring.notifications.models.notification import Notification
    from ring.parties.models.group_model import Group
    from ring.parties.models.user_model import User

QUESTION_SNIPPET_LENGTH = 80


def _display_name(user: User) -> str:
    return user.name or user.email


def _snippet(text: str, limit: int = QUESTION_SNIPPET_LENGTH) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def _joined_names(users: Sequence[User]) -> str:
    names = [_display_name(user) for user in users]
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return f"{', '.join(names[:2])}, and {len(names) - 2} more"


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
    actor = _display_name(added_by)
    return notify_users(
        db,
        recipients,
        type=NotificationType.ADDED_TO_GROUP,
        title=f"You've been added to {group.name}",
        body=f"{actor} added you to the loop.",
        target_api_id=group.api_identifier,
    )


def notify_member_joined(
    db: Session,
    group: Group,
    new_members: Sequence[User],
    actor: User | None = None,
) -> list[Notification]:
    """Notify existing group members that new members joined.

    Fires when users join via the add-members flow or by accepting an
    invite. New members themselves (and the acting user) are not notified.

    Args:
        db (Session): Database session
        group (Group): Group that gained members
        new_members (Sequence[User]): Users who just joined
        actor (User | None): User who added them, if any

    Returns:
        list[Notification]: Created in-app notifications
    """
    if not new_members:
        return []
    excluded_ids = {user.id for user in new_members}
    if actor is not None:
        excluded_ids.add(actor.id)
    recipients = [
        member for member in group.members if member.id not in excluded_ids
    ]
    if not recipients:
        return []
    joined = _joined_names(new_members)
    return notify_users(
        db,
        recipients,
        type=NotificationType.MEMBER_JOINED,
        title=f"{joined} joined {group.name}",
        body="Say hello in your next letter.",
        target_api_id=group.api_identifier,
    )


def notify_new_question(
    db: Session,
    letter: Letter,
    question_text: str,
    asked_by: User,
    author: User | None = None,
) -> list[Notification]:
    """Notify participants that a question was added to an active letter.

    The acting user and the credited author (when different) are not
    notified. No-ops for letters that are no longer collecting content.

    Args:
        db (Session): Database session
        letter (Letter): Letter the question was added to
        question_text (str): Text of the new question
        asked_by (User): User who performed the add
        author (User | None): Credited question author, if any

    Returns:
        list[Notification]: Created in-app notifications
    """
    if letter.status not in (
        LetterStatus.UPCOMING,
        LetterStatus.IN_PROGRESS,
    ):
        return []
    excluded_ids = {asked_by.id}
    if author is not None:
        excluded_ids.add(author.id)
    recipients = [
        user for user in letter.participants if user.id not in excluded_ids
    ]
    if not recipients:
        return []
    asker = _display_name(author or asked_by)
    return notify_users(
        db,
        recipients,
        type=NotificationType.NEW_QUESTION,
        title=f"New question in {letter.group.name}",
        body=f"{asker} asked: “{_snippet(question_text)}”",
        target_api_id=letter.api_identifier,
    )


def notify_new_response(
    db: Session,
    question: Question,
    responder: User,
) -> list[Notification]:
    """Notify a question's author that someone answered their question.

    Only the author is notified, and never about their own answer, so this
    stays high-signal even in chatty groups.

    Args:
        db (Session): Database session
        question (Question): Question that received a new response
        responder (User): User who submitted the response

    Returns:
        list[Notification]: Created in-app notifications
    """
    author = question.author
    if author is None or author.id == responder.id:
        return []
    letter = question.letter
    return notify_users(
        db,
        [author],
        type=NotificationType.NEW_RESPONSE,
        title=f"{_display_name(responder)} answered your question",
        body=(
            f"“{_snippet(question.question_text)}” — in "
            f"{letter_display_title(letter)} for {letter.group.name}"
        ),
        target_api_id=letter.api_identifier,
    )
