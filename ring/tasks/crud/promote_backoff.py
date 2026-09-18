"""Coalesce and back off failed cyclic-letter promote jobs.

``poll_schedule_task`` runs every minute and re-enqueues
``promote_and_create_new_letters`` for the same letter ids whenever
promote is still needed. A persistent error (historically a number-gap
``UniqueViolation``) then fires every minute until the API is restarted.

This module keeps an in-process record of in-flight and recently failed
promote batches so the poller can skip them, and emits a stable ERROR
line for a CloudWatch metric filter.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from loguru import logger

PROMOTE_BACKOFF_BASE = timedelta(minutes=2)
PROMOTE_BACKOFF_CAP = timedelta(minutes=30)
PROMOTE_IN_FLIGHT_TIMEOUT = timedelta(minutes=15)
PROMOTE_FAILURE_LOG = "promote_and_create_new_letters failed"

_IN_FLIGHT: dict[frozenset[int], datetime] = {}
_FAILURES: dict[frozenset[int], tuple[datetime, int]] = {}


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


def should_enqueue_promote(
    letter_ids: list[int], now: datetime | None = None
) -> bool:
    """Return True when a promote job should be scheduled for these ids."""
    if not letter_ids:
        return False
    if now is None:
        now = datetime.now(tz=UTC)
    key = frozenset(letter_ids)
    started_at = _IN_FLIGHT.get(key)
    if started_at is not None and now - started_at < PROMOTE_IN_FLIGHT_TIMEOUT:
        return False
    failure = _FAILURES.get(key)
    if failure is not None:
        failed_at, count = failure
        if now < failed_at + backoff_delay(count):
            return False
    return True


def mark_promote_started(
    letter_ids: list[int], now: datetime | None = None
) -> None:
    """Record that a promote job is in flight for these letter ids."""
    if now is None:
        now = datetime.now(tz=UTC)
    _IN_FLIGHT[frozenset(letter_ids)] = now


def mark_promote_succeeded(letter_ids: list[int]) -> None:
    """Clear in-flight and failure state after a successful promote."""
    key = frozenset(letter_ids)
    _IN_FLIGHT.pop(key, None)
    _FAILURES.pop(key, None)


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
    key = frozenset(letter_ids)
    _IN_FLIGHT.pop(key, None)
    previous = _FAILURES.get(key)
    count = previous[1] + 1 if previous else 1
    _FAILURES[key] = (now, count)
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
    """Enqueue a promote job unless one is in flight or backing off."""
    if now is None:
        now = datetime.now(tz=UTC)
    if not should_enqueue_promote(letter_ids, now):
        logger.warning(
            "Skipping promote enqueue for letter ids {} "
            "(in flight or backing off after failure)",
            letter_ids,
        )
        return False
    mark_promote_started(letter_ids, now)
    add_job(job, args=[letter_ids])  # type: ignore[operator]
    return True
