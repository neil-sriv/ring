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

        email_draft = construct_waiting_response_email(
            recipients,
            group_name,
            letter_api_id,
            letter_title,
        )

        assert email_draft.destination["ToAddresses"] == recipients

        subject = email_draft.message["Subject"]["Data"]
        assert letter_title in subject
        assert "waiting for your response" in subject.lower()
        assert "last day" not in subject.lower()

        html_body = email_draft.message["Body"]["Html"]["Data"]
        text_body = email_draft.message["Body"]["Text"]["Data"]
        letter_url = app_url(f"loops/{letter_api_id}")
        for body in (html_body, text_body):
            assert group_name in body
            assert letter_title in body
            assert letter_url in body
            assert "has not been sent" in body
            assert "waiting for your response" in body
            assert "last day" not in body.lower()

    def test_construct_waiting_response_email_with_custom_title(self) -> None:
        """Custom letter titles appear in subject and body."""
        email_draft = construct_waiting_response_email(
            ["user@example.com"],
            "Friends Newsletter",
            "lttr_xyz789",
            "Summer Edition",
        )

        subject = email_draft.message["Subject"]["Data"]
        html_body = email_draft.message["Body"]["Html"]["Data"]
        text_body = email_draft.message["Body"]["Text"]["Data"]

        assert "Summer Edition" in subject
        assert "Summer Edition" in html_body
        assert "Summer Edition" in text_body


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
