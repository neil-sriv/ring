"""Tests for promote-job coalesce and backoff."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from loguru import logger

from ring.tasks.crud.promote_backoff import (
    PROMOTE_BACKOFF_CAP,
    PROMOTE_FAILURE_LOG,
    backoff_delay,
    enqueue_promote_if_allowed,
    mark_promote_failed,
    mark_promote_started,
    mark_promote_succeeded,
    reset_promote_backoff,
    should_enqueue_promote,
)


@pytest.fixture(autouse=True)
def _clear_backoff_state() -> None:
    reset_promote_backoff()
    yield
    reset_promote_backoff()


class TestPromoteBackoff:
    def test_backoff_delay_caps_at_thirty_minutes(self) -> None:
        assert backoff_delay(1) == timedelta(minutes=2)
        assert backoff_delay(2) == timedelta(minutes=4)
        assert backoff_delay(3) == timedelta(minutes=8)
        assert backoff_delay(5) == PROMOTE_BACKOFF_CAP
        assert backoff_delay(8) == PROMOTE_BACKOFF_CAP

    def test_skips_while_in_flight(self) -> None:
        now = datetime(2026, 9, 18, 14, 0, tzinfo=UTC)
        letter_ids = [4321436]
        mark_promote_started(letter_ids, now)
        assert should_enqueue_promote(letter_ids, now) is False
        assert (
            should_enqueue_promote(letter_ids, now + timedelta(minutes=1))
            is False
        )
        assert (
            should_enqueue_promote(letter_ids, now + timedelta(minutes=16))
            is True
        )

    def test_skips_after_failure_until_backoff_expires(self) -> None:
        now = datetime(2026, 9, 18, 14, 0, tzinfo=UTC)
        letter_ids = [1, 2]
        mark_promote_failed(letter_ids, RuntimeError("boom"), now=now)
        assert should_enqueue_promote(letter_ids, now) is False
        assert (
            should_enqueue_promote(letter_ids, now + timedelta(minutes=1))
            is False
        )
        assert (
            should_enqueue_promote(letter_ids, now + timedelta(minutes=2))
            is True
        )

    def test_success_clears_failure_and_in_flight(self) -> None:
        now = datetime(2026, 9, 18, 14, 0, tzinfo=UTC)
        letter_ids = [9]
        mark_promote_started(letter_ids, now)
        mark_promote_failed(letter_ids, RuntimeError("boom"), now=now)
        mark_promote_succeeded(letter_ids)
        assert should_enqueue_promote(letter_ids, now) is True

    def test_failed_log_uses_stable_metric_string(self) -> None:
        captured: list[str] = []
        handler_id = logger.add(lambda message: captured.append(str(message)))
        try:
            mark_promote_failed([7], ValueError("duplicate key"))
        finally:
            logger.remove(handler_id)
        assert any(PROMOTE_FAILURE_LOG in line for line in captured)
        assert any("duplicate key" in line for line in captured)

    def test_enqueue_coalesces_and_then_allows_retry_after_failure(
        self,
    ) -> None:
        now = datetime(2026, 9, 18, 14, 0, tzinfo=UTC)
        add_job = MagicMock()
        job = object()
        letter_ids = [10]

        assert (
            enqueue_promote_if_allowed(letter_ids, add_job, job, now=now)
            is True
        )
        add_job.assert_called_once_with(job, args=[letter_ids])

        assert (
            enqueue_promote_if_allowed(letter_ids, add_job, job, now=now)
            is False
        )
        assert add_job.call_count == 1

        mark_promote_failed(letter_ids, RuntimeError("boom"), now=now)
        later = now + timedelta(minutes=2)
        assert (
            enqueue_promote_if_allowed(letter_ids, add_job, job, now=later)
            is True
        )
        assert add_job.call_count == 2
