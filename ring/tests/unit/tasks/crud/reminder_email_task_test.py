"""Tests for reminder email day-count copy."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from ring.email_util import EmailDraft
from ring.letters.constants import LetterStatus, LetterType
from ring.lib.app_links import app_url
from ring.tasks.crud.reminder_email_task import construct_reminder_email


def _parts(email_draft: EmailDraft) -> tuple[str, str, str]:
    message = email_draft.message
    return (
        message["Subject"]["Data"],
        message["Body"]["Html"]["Data"],
        message["Body"]["Text"]["Data"],
    )


def _reminder(
    *,
    status: LetterStatus,
    letter_type: LetterType,
    send_at: datetime,
    now: datetime,
    group_name: str = "Family",
) -> EmailDraft:
    return construct_reminder_email(
        ["user@example.com"],
        group_name,
        "lttr_abc",
        status,
        send_at,
        letter_type,
        now=now,
    )


class TestReminderEmailDaysLeft:
    """Subject, preheader, and both bodies share one countdown."""

    def test_three_days_left_to_respond(self) -> None:
        send_at = datetime(2026, 10, 31, 15, tzinfo=UTC)
        draft = _reminder(
            status=LetterStatus.IN_PROGRESS,
            letter_type=LetterType.CYCLIC,
            send_at=send_at,
            now=datetime(2026, 10, 28, 15, tzinfo=UTC),
        )
        subject, html_body, text_body = _parts(draft)
        lead = "3 days left to respond"

        assert subject == "Ring Reminder: 3 days left to respond for Family"
        assert f"{lead} for Family." in html_body
        for body in (html_body, text_body):
            assert lead in body
            assert "1 days" not in body
            assert "0 day" not in body
        letter_url = app_url("loops/lttr_abc")
        assert letter_url in html_body
        assert letter_url in text_body
        assert "link above" not in text_body

    def test_one_day_left_is_singular(self) -> None:
        send_at = datetime(2026, 11, 8, 15, tzinfo=UTC)
        draft = _reminder(
            status=LetterStatus.IN_PROGRESS,
            letter_type=LetterType.CYCLIC,
            send_at=send_at,
            now=send_at - timedelta(days=1),
        )
        subject, html_body, text_body = _parts(draft)

        assert "1 day left to respond" in subject
        assert "1 days" not in subject
        for body in (html_body, text_body):
            assert "1 day left to respond" in body
            assert "1 days" not in body

    def test_cyclic_question_reminder_counts_to_promotion(self) -> None:
        send_at = datetime(2026, 11, 8, 15, tzinfo=UTC)
        draft = _reminder(
            status=LetterStatus.UPCOMING,
            letter_type=LetterType.CYCLIC,
            send_at=send_at,
            now=send_at - timedelta(days=8),
        )
        subject, html_body, text_body = _parts(draft)
        lead = "1 day left to add questions"

        assert subject == (
            "Ring Reminder: 1 day left to add questions for Family"
        )
        assert "8 days" not in subject
        for body in (html_body, text_body):
            assert lead in body
            assert "Add questions" in body or "add questions" in body

    def test_adhoc_question_reminder_counts_to_send(self) -> None:
        send_at = datetime(2026, 11, 8, 15, tzinfo=UTC)
        draft = _reminder(
            status=LetterStatus.UPCOMING,
            letter_type=LetterType.ADHOC,
            send_at=send_at,
            now=send_at - timedelta(days=8),
        )
        subject, html_body, text_body = _parts(draft)

        assert "8 days left to add questions" in subject
        for body in (html_body, text_body):
            assert "8 days left to add questions" in body

    def test_same_day_with_time_left(self) -> None:
        send_at = datetime(2026, 11, 8, 22, tzinfo=UTC)
        draft = _reminder(
            status=LetterStatus.IN_PROGRESS,
            letter_type=LetterType.CYCLIC,
            send_at=send_at,
            now=datetime(2026, 11, 8, 10, tzinfo=UTC),
        )
        subject, html_body, text_body = _parts(draft)
        lead = "Less than a day left to respond"

        assert lead in subject
        for body in (html_body, text_body):
            assert lead in body
            assert "0 day" not in body

    def test_past_deadline_says_today_and_not_a_negative(self) -> None:
        send_at = datetime(2026, 11, 8, 15, tzinfo=UTC)
        draft = _reminder(
            status=LetterStatus.IN_PROGRESS,
            letter_type=LetterType.CYCLIC,
            send_at=send_at,
            now=send_at + timedelta(days=2),
        )
        subject, html_body, text_body = _parts(draft)
        lead = "Today is the last day to respond"

        assert lead in subject
        for part in (subject, html_body, text_body):
            assert lead in part
            assert "-2" not in part
            assert "0 day" not in part
