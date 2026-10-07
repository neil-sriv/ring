"""Coalesce and back off failed cyclic-letter promote jobs.

``poll_schedule_task`` runs every minute and re-enqueues
``promote_and_create_new_letters`` for the same letter ids whenever
promote is still needed. A persistent error (historically a number-gap
``UniqueViolation``) then fires every minute until the API is restarted.

This module keeps an in-process record of in-flight and recently failed
promote letters so the poller can skip them, and emits a stable ERROR
line for a CloudWatch metric filter.

State is keyed **per letter id**, not the exact poll batch. Otherwise a
failed letter A is retried immediately as soon as another group adds B
to the same ``collect_future_letters`` list (``{A} ≠ {A, B}``).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from loguru import logger

PROMOTE_BACKOFF_BASE = timedelta(minutes=2)
PROMOTE_BACKOFF_CAP = timedelta(minutes=30)
PROMOTE_IN_FLIGHT_TIMEOUT = timedelta(minutes=15)
PROMOTE_FAILURE_LOG = "promote_and_create_new_letters failed"

_IN_FLIGHT: dict[int, datetime] = {}
_FAILURES: dict[int, tuple[datetime, int]] = {}


def reset_promote_backoff() -> None:
    """Clear in-process promote backoff state. For tests only."""
    _IN_FLIGHT.clear()
    _FAILURES.clear()


def backoff_delay(failure_count: int) -> timedelta:
    """Return exponential backoff for a 1-based failure count."""
    if failure_count < 1:
        return timedelta(0)
    delay = PROMOTE_BACKOFF_BASE * (2 ** (failure_count - 1))
    if delay > PROMOTE_BACKOFF_CAP:
        return PROMOTE_BACKOFF_CAP
    return delay


def _is_blocked(letter_id: int, now: datetime) -> bool:
    started_at = _IN_FLIGHT.get(letter_id)
    if started_at is not None and now - started_at < PROMOTE_IN_FLIGHT_TIMEOUT:
        return True
    failure = _FAILURES.get(letter_id)
    if failure is not None:
        failed_at, count = failure
        if now < failed_at + backoff_delay(count):
            return True
    return False


def eligible_promote_ids(
    letter_ids: list[int], now: datetime | None = None
) -> list[int]:
    """Return letter ids that are neither in flight nor backing off."""
    if now is None:
        now = datetime.now(tz=UTC)
    return [
        letter_id
        for letter_id in letter_ids
        if not _is_blocked(letter_id, now)
    ]


def should_enqueue_promote(
    letter_ids: list[int], now: datetime | None = None
) -> bool:
    """Return True when at least one of these letters may be promoted."""
    return bool(eligible_promote_ids(letter_ids, now))


def mark_promote_started(
    letter_ids: list[int], now: datetime | None = None
) -> None:
    """Record that a promote job is in flight for each letter id."""
    if now is None:
        now = datetime.now(tz=UTC)
    for letter_id in letter_ids:
        _IN_FLIGHT[letter_id] = now


def mark_promote_succeeded(letter_ids: list[int]) -> None:
    """Clear in-flight and failure state after a successful promote."""
    for letter_id in letter_ids:
        _IN_FLIGHT.pop(letter_id, None)
        _FAILURES.pop(letter_id, None)


def mark_promote_failed(
    letter_ids: list[int],
    exc: BaseException,
    now: datetime | None = None,
) -> None:
    """Record a promote failure, clear in-flight, and log a stable ERROR.

    The log line always contains ``promote_and_create_new_letters failed``
    so CloudWatch can alarm on it. See docs/infrastructure.md.
    """
    if now is None:
        now = datetime.now(tz=UTC)
    for letter_id in letter_ids:
        _IN_FLIGHT.pop(letter_id, None)
        previous = _FAILURES.get(letter_id)
        count = previous[1] + 1 if previous else 1
        _FAILURES[letter_id] = (now, count)
    logger.error(
        "{} for letter ids {}: {}",
        PROMOTE_FAILURE_LOG,
        letter_ids,
        exc,
    )


def enqueue_promote_if_allowed(
    letter_ids: list[int],
    add_job: object,
    job: object,
    now: datetime | None = None,
) -> bool:
    """Enqueue a promote job for ids that are not in flight or backing off."""
    if now is None:
        now = datetime.now(tz=UTC)
    eligible = eligible_promote_ids(letter_ids, now)
    if not eligible:
        logger.warning(
            "Skipping promote enqueue for letter ids {} "
            "(in flight or backing off after failure)",
            letter_ids,
        )
        return False
    skipped = [
        letter_id for letter_id in letter_ids if letter_id not in set(eligible)
    ]
    if skipped:
        logger.warning(
            "Skipping promote enqueue for letter ids {} "
            "(in flight or backing off after failure); enqueueing {}",
            skipped,
            eligible,
        )
    mark_promote_started(eligible, now)
    add_job(job, args=[eligible])  # type: ignore[operator]
    return True
