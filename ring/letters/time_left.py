"""Calendar-day countdown for deadline warning emails.

Matches ``daysUntil`` in ``react/src/util/loopTime.ts``: whole calendar days,
not elapsed 24-hour chunks. The frontend uses the viewer's local calendar.
These emails are rendered once on the server, which compares ``send_at`` in
UTC (the scheduler timezone and ``has_send_date_arrived``), so the calendar
here is UTC.
"""

from __future__ import annotations

from datetime import UTC, datetime

from ring.letters.constants import (
    LETTER_PROMOTION_LOOKAHEAD,
    LetterStatus,
    LetterType,
)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def calendar_days_until(deadline: datetime, now: datetime) -> int:
    """Signed UTC calendar days from ``now`` until ``deadline``.

    A deadline later today is 0. A deadline yesterday is negative. Naive
    datetimes are treated as UTC, matching the rest of the send-time checks.
    """
    return (_as_utc(deadline).date() - _as_utc(now).date()).days


def days_left_label(deadline: datetime, now: datetime | None = None) -> str:
    """Non-negative countdown label.

    ``"3 days"``, ``"1 day"``, ``"less than a day"`` (same UTC date, still
    in the future), or ``"today"`` once the deadline has passed. Never
    ``"0 days"`` and never a negative count.
    """
    current = _as_utc(now or datetime.now(tz=UTC))
    days = calendar_days_until(deadline, current)
    if days > 1:
        return f"{days} days"
    if days == 1:
        return "1 day"
    if _as_utc(deadline) > current:
        return "less than a day"
    return "today"


def days_left_to(
    action: str, deadline: datetime, now: datetime | None = None
) -> str:
    """Sentence lead such as ``"3 days left to respond"``."""
    label = days_left_label(deadline, now)
    if label == "today":
        return f"Today is the last day to {action}"
    if label == "less than a day":
        return f"Less than a day left to {action}"
    return f"{label} left to {action}"


def reminder_deadline(
    send_at: datetime,
    letter_status: str,
    letter_type: str,
) -> datetime:
    """Deadline the reminder email is counting toward.

    Cyclic upcoming letters are still in the question phase. That phase
    ends when the letter is promoted, ``LETTER_PROMOTION_LOOKAHEAD`` before
    ``send_at``. Response reminders, and adhoc letters (they are not
    auto-promoted), count down to ``send_at``.
    """
    if (
        letter_status == LetterStatus.UPCOMING
        and letter_type == LetterType.CYCLIC
    ):
        return send_at - LETTER_PROMOTION_LOOKAHEAD
    return send_at
