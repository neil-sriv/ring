"""Tests for waiting-response email construction."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from ring.letters.constants import LetterStatus
from ring.lib.app_links import app_url
from ring.tasks.crud.waiting_response_email_task import (
    construct_waiting_response_email,
    letter_display_title,
    letter_non_responder_emails,
)
from ring.tests.factories.letters.letter_factory import LetterFactory
from ring.tests.factories.letters.question_factory import QuestionFactory
from ring.tests.factories.letters.response_factory import ResponseFactory
from ring.tests.factories.parties.group_factory import GroupFactory
from ring.tests.factories.parties.user_factory import UserFactory


class TestWaitingResponseEmailTask:
    """Test suite for waiting-response email construction."""

    def test_construct_waiting_response_email(self) -> None:
        """Draft includes group, letter, link, and waiting-response copy."""
        recipients = ["user1@example.com", "user2@example.com"]
        group_name = "Test Group"
        letter_api_id = "lttr_123abc"
        letter_title = "#5"

        send_at = datetime.now(tz=UTC) + timedelta(days=3)
        email_draft = construct_waiting_response_email(
            recipients,
            group_name,
            letter_api_id,
            letter_title,
            send_at,
            now=send_at - timedelta(days=3),
        )

        assert email_draft.destination["ToAddresses"] == recipients

        subject = email_draft.message["Subject"]["Data"]
        assert letter_title in subject
        assert "waiting for your response" in subject.lower()
        assert "3 days left" in subject
        assert "last day" not in subject.lower()

        html_body = email_draft.message["Body"]["Html"]["Data"]
        text_body = email_draft.message["Body"]["Text"]["Data"]
        letter_url = app_url(f"loops/{letter_api_id}")
        preheader = "3 days left to respond."
        for body in (html_body, text_body):
            assert group_name in body
            assert letter_title in body
            assert letter_url in body
            assert "has not been sent" in body
            assert "waiting for your response" in body
            assert "3 days left to respond" in body
            assert "last day" not in body.lower()
            assert "-1" not in body
        assert preheader in html_body

    def test_construct_waiting_response_email_with_custom_title(self) -> None:
        """Custom letter titles appear in subject and body."""
        send_at = datetime(2026, 11, 2, 15, tzinfo=UTC)
        email_draft = construct_waiting_response_email(
            ["user@example.com"],
            "Friends Newsletter",
            "lttr_xyz789",
            "Summer Edition",
            send_at,
            now=datetime(2026, 11, 1, 15, tzinfo=UTC),
        )

        subject = email_draft.message["Subject"]["Data"]
        html_body = email_draft.message["Body"]["Html"]["Data"]
        text_body = email_draft.message["Body"]["Text"]["Data"]

        assert "Summer Edition" in subject
        assert "1 day left" in subject
        assert "1 days" not in subject
        assert "Summer Edition" in html_body
        assert "1 day left to respond" in html_body
        assert "Summer Edition" in text_body
        assert "1 day left to respond" in text_body

    def test_same_day_and_overdue_never_say_last_day_or_a_negative(
        self,
    ) -> None:
        """The deferred send can slip, but the copy stays non-negative."""
        same_day = construct_waiting_response_email(
            ["user@example.com"],
            "Test Group",
            "lttr_123abc",
            "#5",
            datetime(2026, 11, 1, 18, tzinfo=UTC),
            now=datetime(2026, 11, 1, 10, tzinfo=UTC),
        )
        overdue = construct_waiting_response_email(
            ["user@example.com"],
            "Test Group",
            "lttr_123abc",
            "#5",
            datetime(2026, 10, 31, 10, tzinfo=UTC),
            now=datetime(2026, 11, 2, 10, tzinfo=UTC),
        )

        same_subject = same_day.message["Subject"]["Data"]
        same_html = same_day.message["Body"]["Html"]["Data"]
        same_text = same_day.message["Body"]["Text"]["Data"]
        assert "less than a day left" in same_subject
        for body in (same_html, same_text):
            assert "Less than a day left to respond" in body
            assert "last day" not in body.lower()
            assert "0 day" not in body

        overdue_subject = overdue.message["Subject"]["Data"]
        overdue_html = overdue.message["Body"]["Html"]["Data"]
        overdue_text = overdue.message["Body"]["Text"]["Data"]
        assert "due today" in overdue_subject
        for part in (overdue_subject, overdue_html, overdue_text):
            assert "last day" not in part.lower()
            assert "-2" not in part
            assert "0 day" not in part
        for body in (overdue_html, overdue_text):
            assert "Due today" in body


class TestWaitingResponseRecipients:
    """Helpers for choosing waiting-response email recipients and titles."""

    def test_letter_non_responder_emails_excludes_responders(
        self, db_session: Session
    ) -> None:
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=datetime.now(tz=UTC) + timedelta(days=1),
        )
        question = QuestionFactory.create(letter=letter)
        ResponseFactory.create(question=question, participant=members[0])
        db_session.commit()

        assert set(letter_non_responder_emails(letter)) == {
            member.email for member in members[1:]
        }

    def test_letter_non_responder_emails_empty_when_everyone_answered(
        self, db_session: Session
    ) -> None:
        admin = UserFactory.create()
        members = [admin] + [UserFactory.create() for _ in range(3)]
        group = GroupFactory.create(admin=admin, members=members)
        letter = LetterFactory.create(
            group=group,
            status=LetterStatus.IN_PROGRESS,
            send_at=datetime.now(tz=UTC) + timedelta(days=1),
        )
        question = QuestionFactory.create(letter=letter)
        for member in members:
            ResponseFactory.create(question=question, participant=member)
        db_session.commit()

        assert letter_non_responder_emails(letter) == []

    def test_letter_display_title_prefers_custom_title(
        self, db_session: Session
    ) -> None:
        letter = LetterFactory.create(
            status=LetterStatus.IN_PROGRESS,
            send_at=datetime.now(tz=UTC) + timedelta(days=1),
            title="Summer Edition",
        )
        db_session.commit()
        assert letter_display_title(letter) == "Summer Edition"

    def test_letter_display_title_falls_back_to_number(
        self, db_session: Session
    ) -> None:
        letter = LetterFactory.create(
            status=LetterStatus.IN_PROGRESS,
            send_at=datetime.now(tz=UTC) + timedelta(days=1),
        )
        db_session.commit()
        assert letter_display_title(letter) == f"#{letter.number}"
