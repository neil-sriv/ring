"""Send-threshold helpers for deferring letter sends until enough members respond."""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from numbers import Real
from typing import TYPE_CHECKING, Any

from loguru import logger

from ring.letters.constants import LetterStatus

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from ring.letters.models.letter_model import Letter
    from ring.parties.models.group_model import Group

GROUP_SETTING_MIN_RESPONDERS_KEY = "letter_send_min_responders"
GROUP_SETTING_MIN_RESPONDER_RATIO_KEY = "letter_send_min_responder_ratio"
DEFAULT_MIN_RESPONDER_RATIO_TO_SEND = 0.5
LETTER_SEND_DEFERRAL_DAYS = 1


def parse_positive_int(value: Any) -> int | None:
    """Parse a value into a positive integer, returning None if invalid."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    if isinstance(value, float):
        if value.is_integer() and value > 0:
            return int(value)
        return None
    if isinstance(value, str):
        try:
            parsed = float(value)
        except ValueError:
            return None
        if parsed.is_integer() and parsed > 0:
            return int(parsed)
    return None


def parse_ratio(value: Any) -> float | None:
    """Parse a value into a ratio in the [0, 1] range."""
    if isinstance(value, bool):
        return None
    if isinstance(value, str):
        try:
            value = float(value)
        except ValueError:
            return None
    elif not isinstance(value, Real):
        return None
    ratio = float(value)
    if ratio < 0 or ratio > 1:
        return None
    return ratio


def is_send_threshold_disabled(group: Group) -> bool:
    """Return True when the group has explicitly disabled the send threshold."""
    ratio_setting = group.key_values.get_value(
        GROUP_SETTING_MIN_RESPONDER_RATIO_KEY
    )
    if ratio_setting is None:
        return False
    configured_ratio = parse_ratio(ratio_setting)
    return configured_ratio == 0.0


def get_group_min_responder_ratio(group: Group) -> float | None:
    """Return the configured responder ratio, or None when using the default."""
    ratio_setting = group.key_values.get_value(
        GROUP_SETTING_MIN_RESPONDER_RATIO_KEY
    )
    if ratio_setting is None:
        return None
    configured_ratio = parse_ratio(ratio_setting)
    if configured_ratio is None:
        return None
    return configured_ratio


def effective_send_threshold_ratio(group: Group) -> float | None:
    """Return the effective ratio used for send gating, or None when disabled."""
    if (
        parse_positive_int(
            group.key_values.get_value(GROUP_SETTING_MIN_RESPONDERS_KEY)
        )
        is not None
    ):
        return None
    configured_ratio = get_group_min_responder_ratio(group)
    if configured_ratio is not None:
        if configured_ratio == 0.0:
            return None
        return configured_ratio
    return DEFAULT_MIN_RESPONDER_RATIO_TO_SEND


def set_group_min_responder_ratio(group: Group, ratio: float | None) -> None:
    """Persist the group's minimum responder ratio in key-values."""
    if ratio is None:
        group.key_values.delete_value(GROUP_SETTING_MIN_RESPONDER_RATIO_KEY)
        return
    parsed = parse_ratio(ratio)
    if parsed is None:
        raise ValueError("min_responder_ratio must be between 0 and 1")
    group.key_values.set_value(GROUP_SETTING_MIN_RESPONDER_RATIO_KEY, parsed)


def minimum_responders_required(letter: Letter) -> int:
    """Return the minimum unique responder count required to send.

    Group-level configuration (stored in group key-values):
    - `letter_send_min_responders`: positive integer responder count
    - `letter_send_min_responder_ratio`: ratio in [0, 1]; 0 disables the gate
    """
    participant_count = len(letter.participants)
    if participant_count <= 0:
        return 0

    min_responders_setting = letter.group.key_values.get_value(
        GROUP_SETTING_MIN_RESPONDERS_KEY
    )
    configured_min_responders = parse_positive_int(min_responders_setting)
    if configured_min_responders is not None:
        return min(participant_count, configured_min_responders)

    configured_ratio = get_group_min_responder_ratio(letter.group)
    if configured_ratio is not None:
        if configured_ratio == 0.0:
            return 0
        return max(1, math.ceil(participant_count * configured_ratio))

    return max(
        1, math.ceil(participant_count * DEFAULT_MIN_RESPONDER_RATIO_TO_SEND)
    )


def letter_responder_count(letter: Letter) -> int:
    """Return the number of unique current participants who have responded.

    Responders who are no longer participants (e.g. members removed from
    the group while the letter was open) are excluded so the count stays
    consistent with the participant-based threshold denominator. Their
    responses remain part of the letter and the reply tracker still
    shows them.
    """
    return len(set(letter.responders) & set(letter.participants))


def is_below_send_threshold(letter: Letter) -> bool:
    """Return True when fewer participants responded than required to send."""
    required_responders = minimum_responders_required(letter)
    if required_responders <= 0:
        return False
    return letter_responder_count(letter) < required_responders


def has_send_date_arrived(letter: Letter, now: datetime | None = None) -> bool:
    """Return True once the letter's send date has been reached."""
    return letter.send_at <= (now or datetime.now(tz=UTC))


def defer_letter_send(db: Session, letter: Letter) -> bool:
    """Push a letter's send date out by the deferral interval.

    Idempotent across callers that may both run at the same deadline moment
    (send-email task and postpend): once ``send_at`` is in the future, further
    calls are a no-op. A successful deferral also schedules a one-shot email
    to participants who have not yet responded.

    Returns:
        True if the send date was deferred, False if it had not yet arrived
        (or had already been deferred into the future).
    """
    # Imported here because ring.letters.crud.letter imports this module.
    from ring.letters.crud import letter as letter_crud

    if not has_send_date_arrived(letter):
        return False

    new_send_at = letter.send_at + timedelta(days=LETTER_SEND_DEFERRAL_DAYS)
    logger.info(
        "Deferring letter {} send from {} to {}: responders {}/{}".format(
            letter.id,
            letter.send_at,
            new_send_at,
            letter_responder_count(letter),
            minimum_responders_required(letter),
        )
    )
    letter_crud.edit_letter(db, letter, send_at=new_send_at)
    _schedule_waiting_response_email(letter.id)
    return True


def _schedule_waiting_response_email(letter_id: int) -> None:
    """Queue a one-shot job to email participants who have not responded.

    Imported lazily because ``ring.tasks.crud.task`` imports this module.
    """
    from ring.async_scheduler.scheduler import scheduler
    from ring.tasks.crud.task import send_waiting_response_email

    scheduler.add_job(
        send_waiting_response_email,
        args=[letter_id],
    )


def defer_letter_send_if_below_threshold(db: Session, letter: Letter) -> bool:
    """Defer a letter's send date when the responder threshold is not met.

    Intended for the send-email task, which runs when the send date arrives.

    Returns:
        True if the send was deferred, False otherwise.
    """
    if letter.status != LetterStatus.IN_PROGRESS:
        return False

    if not is_below_send_threshold(letter):
        return False

    return defer_letter_send(db, letter)


def hold_letter_for_send_threshold(db: Session, letter: Letter) -> bool:
    """Return True when a letter must not be marked SENT yet.

    Called by the postpend job once a letter's send date has arrived; the
    caller is responsible for not postpending letters before their deadline.
    Deferral is idempotent via ``defer_letter_send``, so a concurrent
    send-email task that already pushed ``send_at`` will not stack a second
    day.

    Returns:
        True if the letter is below its send threshold, False otherwise.
    """
    if letter.status != LetterStatus.IN_PROGRESS:
        return False

    if not is_below_send_threshold(letter):
        return False

    defer_letter_send(db, letter)
    return True
