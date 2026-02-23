"""Tests for response open email task.

This module contains tests for the response open email task,
which sends notifications when a recurring newsletter becomes
open for responses.
"""

from __future__ import annotations

from ring.tasks.crud.response_open_email_task import (
    construct_response_open_email,
)


class TestResponseOpenEmailTask:
    """Test suite for response open email task construction."""

    def test_construct_response_open_email(self) -> None:
        """Test constructing a response open email draft.

        This test verifies that:
        1. An email draft is created with the correct recipients
        2. The email subject contains the letter title
        3. The HTML body contains the group name and letter link
        4. The plain text body contains the group name
        """
        recipients = ["user1@example.com", "user2@example.com"]
        group_name = "Test Group"
        letter_api_id = "let_123abc"
        letter_title = "#5"

        email_draft = construct_response_open_email(
            recipients,
            group_name,
            letter_api_id,
            letter_title,
        )

        # Check recipients
        assert email_draft.destination["ToAddresses"] == recipients

        # Check subject contains letter title
        subject = email_draft.message["Subject"]["Data"]
        assert letter_title in subject
        assert "open for responses" in subject

        # Check HTML body contains group name and link
        html_body = email_draft.message["Body"]["Html"]["Data"]
        assert group_name in html_body
        assert letter_api_id in html_body
        assert letter_title in html_body
        assert "http://ring.neilsriv.tech/loops/" in html_body

        # Check plain text body
        text_body = email_draft.message["Body"]["Text"]["Data"]
        assert group_name in text_body
        assert letter_api_id in text_body
        assert letter_title in text_body

    def test_construct_response_open_email_with_custom_title(self) -> None:
        """Test constructing a response open email with a custom title.

        This test verifies that:
        1. A custom letter title is used in the email
        2. The email structure remains correct
        """
        recipients = ["user@example.com"]
        group_name = "Friends Newsletter"
        letter_api_id = "let_xyz789"
        letter_title = "Summer Edition"

        email_draft = construct_response_open_email(
            recipients,
            group_name,
            letter_api_id,
            letter_title,
        )

        # Check subject contains custom title
        subject = email_draft.message["Subject"]["Data"]
        assert letter_title in subject

        # Check HTML body contains custom title
        html_body = email_draft.message["Body"]["Html"]["Data"]
        assert letter_title in html_body

        # Check plain text body contains custom title
        text_body = email_draft.message["Body"]["Text"]["Data"]
        assert letter_title in text_body
