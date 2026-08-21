"""Tests for letter send email task construction."""

from __future__ import annotations

from ring.email_template import PRIMARY
from ring.tasks.crud.send_email_task import (
    construct_question_html,
    construct_response_html,
    construct_send_letter_email,
)


class TestSendEmailTask:
    """Test suite for issue/letter send email formatting."""

    def test_construct_response_html_preserves_newlines(self) -> None:
        response = ("Alice: Line one\nLine two", [])

        html_body = construct_response_html(response)

        assert "white-space:pre-line" in html_body
        assert "Line one\nLine two" in html_body
        assert "Line one" in html_body
        assert "Line two" in html_body
        assert "Alice" in html_body

    def test_construct_response_html_linkifies_urls(self) -> None:
        response = (
            "Bob: See https://example.com/path for details",
            [],
        )

        html_body = construct_response_html(response)

        assert (
            f'<a href="https://example.com/path" '
            f'style="color:{PRIMARY};text-decoration:underline;">'
            "https://example.com/path</a>"
        ) in html_body

    def test_construct_response_html_escapes_html_characters(self) -> None:
        response = ("Carol: Use <b>tags</b> & ampersands", [])

        html_body = construct_response_html(response)

        assert "&lt;b&gt;tags&lt;/b&gt; &amp; ampersands" in html_body
        assert "<b>tags</b>" not in html_body

    def test_construct_question_html_escapes_question_text(self) -> None:
        html_body = construct_question_html(
            "What is <script>alert(1)</script>?",
            [],
        )

        assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html_body
        assert "<script>" not in html_body

    def test_construct_send_letter_email_includes_formatted_responses(
        self,
    ) -> None:
        letter_dict = {
            "Favorite memory?": [
                ("Dana: First line\nSecond line", []),
            ],
        }

        email_draft = construct_send_letter_email(
            ["user@example.com"],
            "Ring Newsletter #1 for Friends",
            "lttr_abc123",
            letter_dict,
        )

        html_body = email_draft.message["Body"]["Html"]["Data"]
        text_body = email_draft.message["Body"]["Text"]["Data"]

        assert "white-space:pre-line" in html_body
        assert "First line" in html_body
        assert "Second line" in html_body
        assert "Dana: First line\nSecond line" in text_body
