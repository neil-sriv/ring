"""Tests for UTC calendar-day countdowns used in warning emails."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

from ring.letters.constants import LetterStatus, LetterType
from ring.letters.time_left import (
    calendar_days_until,
    days_left_label,
    days_left_to,
    reminder_deadline,
)


class TestCalendarDaysUntil:
    """Day counts follow UTC dates, including the edges around midnight."""

    def test_counts_whole_utc_dates(self) -> None:
        now = datetime(2026, 10, 28, 15, tzinfo=UTC)
        deadline = datetime(2026, 10, 31, 15, tzinfo=UTC)

        assert calendar_days_until(deadline, now) == 3

    def test_one_calendar_day_is_singular(self) -> None:
        now = datetime(2026, 10, 30, 15, tzinfo=UTC)
        deadline = datetime(2026, 10, 31, 15, tzinfo=UTC)

        assert calendar_days_until(deadline, now) == 1
        assert days_left_label(deadline, now) == "1 day"
        assert days_left_to("respond", deadline, now) == (
            "1 day left to respond"
        )

    def test_plural_days(self) -> None:
        now = datetime(2026, 10, 28, 15, tzinfo=UTC)
        deadline = datetime(2026, 10, 31, 15, tzinfo=UTC)

        assert days_left_label(deadline, now) == "3 days"
        assert days_left_to("respond", deadline, now) == (
            "3 days left to respond"
        )

    def test_crossing_midnight_is_one_day_even_under_24_hours(self) -> None:
        now = datetime(2026, 10, 31, 23, 30, tzinfo=UTC)
        deadline = datetime(2026, 11, 1, 0, 30, tzinfo=UTC)

        assert calendar_days_until(deadline, now) == 1
        assert days_left_label(deadline, now) == "1 day"

    def test_same_utc_date_with_time_left_is_less_than_a_day(self) -> None:
        now = datetime(2026, 10, 31, 10, tzinfo=UTC)
        deadline = datetime(2026, 10, 31, 22, tzinfo=UTC)

        assert calendar_days_until(deadline, now) == 0
        assert days_left_label(deadline, now) == "less than a day"
        assert days_left_to("respond", deadline, now) == (
            "Less than a day left to respond"
        )

    def test_same_utc_date_after_the_deadline_is_today(self) -> None:
        now = datetime(2026, 10, 31, 22, tzinfo=UTC)
        deadline = datetime(2026, 10, 31, 15, tzinfo=UTC)

        assert calendar_days_until(deadline, now) == 0
        assert days_left_label(deadline, now) == "today"
        assert days_left_to("add questions", deadline, now) == (
            "Today is the last day to add questions"
        )

    def test_exact_deadline_instant_is_today(self) -> None:
        instant = datetime(2026, 10, 31, 15, tzinfo=UTC)

        assert calendar_days_until(instant, instant) == 0
        assert days_left_label(instant, instant) == "today"

    def test_past_deadline_never_goes_negative(self) -> None:
        now = datetime(2026, 11, 2, 12, tzinfo=UTC)
        deadline = datetime(2026, 10, 31, 12, tzinfo=UTC)

        assert calendar_days_until(deadline, now) == -2
        label = days_left_label(deadline, now)
        clause = days_left_to("respond", deadline, now)

        assert label == "today"
        assert clause == "Today is the last day to respond"
        assert "-" not in label
        assert "0 day" not in clause

    def test_converts_offsets_to_utc_before_taking_the_date(self) -> None:
        # 20:00 at UTC-7 is 03:00 the next day in UTC.
        deadline = datetime(
            2026, 10, 31, 20, tzinfo=timezone(timedelta(hours=-7))
        )
        now = datetime(2026, 10, 31, 22, tzinfo=UTC)

        assert calendar_days_until(deadline, now) == 1

    def test_naive_deadline_is_treated_as_utc(self) -> None:
        now = datetime(2026, 10, 29, 15, tzinfo=UTC)
        deadline = datetime(2026, 11, 1, 15)

        assert calendar_days_until(deadline, now) == 3
        assert days_left_label(deadline, now) == "3 days"


class TestReminderDeadline:
    """Question reminders and response reminders do not share a deadline."""

    def test_cyclic_upcoming_closes_at_promotion(self) -> None:
        send_at = datetime(2026, 11, 8, 15, tzinfo=UTC)

        deadline = reminder_deadline(
            send_at, LetterStatus.UPCOMING, LetterType.CYCLIC
        )

        assert deadline == send_at - timedelta(days=7)
        # The reminder itself is scheduled one day before promotion.
        assert days_left_to(
            "add questions", deadline, send_at - timedelta(days=8)
        ) == ("1 day left to add questions")

    def test_in_progress_closes_at_send(self) -> None:
        send_at = datetime(2026, 11, 8, 15, tzinfo=UTC)

        deadline = reminder_deadline(
            send_at, LetterStatus.IN_PROGRESS, LetterType.CYCLIC
        )

        assert deadline == send_at
        assert days_left_to(
            "respond", deadline, send_at - timedelta(days=1)
        ) == ("1 day left to respond")

    def test_adhoc_upcoming_counts_down_to_send(self) -> None:
        send_at = datetime(2026, 11, 8, 15, tzinfo=UTC)

        deadline = reminder_deadline(
            send_at, LetterStatus.UPCOMING, LetterType.ADHOC
        )

        assert deadline == send_at
        assert days_left_label(deadline, send_at - timedelta(days=8)) == (
            "8 days"
        )
