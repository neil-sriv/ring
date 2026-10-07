"""Create the next upcoming cyclic letter for a group.

Ops path so recovery does not hand-write INSERT SQL (the Aug 2025 SES
recovery created texas exes #24 with only group defaults and locked in
the #16 number gap).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from ring.api_identifier import util as api_identifier_crud
from ring.letters.crud.letter import (
    create_letter_with_questions,
    ensure_upcoming_cyclic_letter,
)
from ring.letters.models.letter_model import Letter
from ring.parties.models.group_model import Group

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class CreateNextLetterError(ValueError):
    """The group has no cyclic letter to advance from."""


def create_next_cyclic_letter(db: Session, group_api_id: str) -> Letter:
    """Return the group's upcoming cyclic letter, creating one if missing.

    Prefer ``ensure_upcoming_cyclic_letter`` when an in-progress letter
    exists. If the group only has SENT (or no in-progress) cyclic letters,
    create the next letter after the highest-numbered one so a fully
    closed cadence can still be restarted without raw SQL.
    """
    group = api_identifier_crud.get_model(db, Group, api_id=group_api_id)
    if group.upcoming_letters:
        return group.upcoming_letters[0]
    created = ensure_upcoming_cyclic_letter(db, group)
    if created is not None:
        return created
    if not group.cyclic_letters:
        raise CreateNextLetterError(
            f"group {group_api_id} has no cyclic letters to advance from"
        )
    latest = max(
        group.cyclic_letters,
        key=lambda letter: (letter.number is not None, letter.number or 0),
    )
    cycle = timedelta(days=group.cycle_length)
    send_at = max(latest.send_at + cycle, datetime.now(tz=UTC) + cycle)
    return create_letter_with_questions(
        db,
        group.api_identifier,
        send_at,
    )
