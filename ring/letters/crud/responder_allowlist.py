"""Helpers for group- and letter-level responder allowlists.

When an allowlist is empty, all group members may respond. When non-empty, only
listed members may respond. Letter-level allowlist overrides the group default
for that letter.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from ring.letters.models.letter_model import Letter
from ring.parties.models.group_model import Group
from ring.parties.models.user_model import User


def effective_responders_for_letter(letter: Letter) -> list[User]:
    """Return users who may submit responses for this letter."""
    return letter.effective_responders


def validate_responder_subset(group: Group, users: list[User]) -> None:
    """Ensure every user is a member of the group."""
    member_ids = {m.id for m in group.members}
    for u in users:
        if u.id not in member_ids:
            raise ValueError(
                "Responder allowlist may only include members of the group.",
            )


def set_group_responder_allowlist(
    db: Session,
    group: Group,
    users: list[User],
) -> Group:
    """Replace the group's responder allowlist (empty = everyone can respond)."""
    validate_responder_subset(group, users)
    group.responder_allowlist = users
    db.add(group)
    return group


def set_letter_responder_allowlist(
    db: Session,
    letter: Letter,
    users: list[User],
) -> Letter:
    """Replace a letter's responder allowlist (empty = use group default)."""
    validate_responder_subset(letter.group, users)
    letter.responder_allowlist = users
    db.add(letter)
    return letter


def sync_allowlists_after_member_added(
    db: Session,
    group: Group,
    user: User,
) -> None:
    """Add a new member to non-empty allowlists on the group and active letters."""
    if group.responder_allowlist:
        if user not in group.responder_allowlist:
            group.responder_allowlist.append(user)
    for letter in group.letters:
        if letter.responder_allowlist and user not in letter.responder_allowlist:
            letter.responder_allowlist.append(user)
    db.add(group)


def sync_allowlists_after_member_removed(
    db: Session,
    group: Group,
    user: User,
) -> None:
    """Remove a user from allowlists when they leave the group."""
    if user in group.responder_allowlist:
        group.responder_allowlist.remove(user)
    for letter in group.letters:
        if user in letter.responder_allowlist:
            letter.responder_allowlist.remove(user)
    db.add(group)
