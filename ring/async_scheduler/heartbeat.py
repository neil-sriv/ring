"""In-process heartbeat for the scheduler's poll job.

The public /version endpoint exposes this so a plain curl against prod can
tell whether the scheduler is alive and when it last completed a poll.
"""

from __future__ import annotations

import threading
from datetime import UTC, datetime

_lock = threading.Lock()
_last_poll_completed_at: datetime | None = None


def record_poll_completed() -> None:
    """Record that a schedule poll just finished successfully."""
    global _last_poll_completed_at
    with _lock:
        _last_poll_completed_at = datetime.now(tz=UTC)


def last_poll_completed_at() -> datetime | None:
    """Return when the scheduler last completed a poll, if ever."""
    with _lock:
        return _last_poll_completed_at
