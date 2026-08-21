"""Utilities for constructing letter send email tasks.

This module provides functions for creating email drafts that contain letter content,
including questions and responses with optional images. The emails are formatted
in both HTML and plain text versions.
"""

from __future__ import annotations

import html
import re

from ring.email_template import (
    BORDER,
    CARD_BG,
    INK,
    MUTED_INK,
    PRIMARY,
    SANS,
    SERIF,
    render_button,
    render_email_shell,
    render_muted_line,
)
from ring.email_util import EmailDraft, construct_email_draft
from ring.lib.app_links import app_url

_URL_RE = re.compile(r"https?://[^\s<>\"]+")


def _split_response_display(response_text: str) -> tuple[str | None, str]:
    """Split a compiled response into participant name and body text."""
    if ": " in response_text:
        name, _, body = response_text.partition(": ")
        return name, body
    return None, response_text


def _linkify_escaped_text(escaped_text: str) -> str:
    """Turn http(s) URLs in already-escaped text into anchor tags."""

    def replacer(match: re.Match[str]) -> str:
        url = match.group(0)
        return (
            f'<a href="{url}" style="color:{PRIMARY};text-decoration:underline;">'
            f"{url}</a>"
        )

    return _URL_RE.sub(replacer, escaped_text)


def _format_response_body_html(text: str) -> str:
    """Format response body text for HTML email bodies."""
    return _linkify_escaped_text(html.escape(text))


def construct_question_html(
    question: str, responses: list[tuple[str, list[str]]]
) -> str:
    """Construct HTML for a question and its responses.

    Args:
        question: The question text
        responses: List of tuples containing (response text, list of image URLs)

    Returns:
        str: HTML string containing the formatted question and responses
    """
    return """
<div style="margin-top: 28px;">
  <h2 style="margin: 0 0 10px; font-family: {serif}; font-size: 18px; line-height: 1.4; font-weight: 600; color: {ink};">
    {question}
  </h2>
  <ul style="margin: 0; padding: 0;">
    {responses}
  </ul>
</div>
""".format(
        serif=SERIF,
        ink=INK,
        question=html.escape(question),
        responses="".join(
            [construct_response_html(response) for response in responses]
        ),
    )


def construct_response_html(response: tuple[str, list[str]]) -> str:
    """Construct HTML for a single response with optional images.

    Args:
        response: Tuple containing (response text, list of image URLs)

    Returns:
        str: HTML string containing the formatted response and images
    """
    participant_name, body = _split_response_display(response[0])
    name_html = (
        (
            '<div style="font-family:{sans};font-weight:600;font-size:14px;'
            'color:{ink};margin-bottom:4px;">{name}</div>'
        ).format(sans=SANS, ink=INK, name=html.escape(participant_name))
        if participant_name
        else ""
    )
    body_html = (
        '<p style="margin:0;font-family:{sans};font-size:14px;'
        'line-height:1.6;color:{ink};white-space:pre-line;">{text}</p>'
    ).format(sans=SANS, ink=INK, text=_format_response_body_html(body))
    image_htmls = "".join(
        [
            (
                '<img src="{url}" alt="Image" '
                'style="display:block; margin:8px 0 0; width:auto; '
                "height:auto; max-width:100%; border-radius:6px; "
                'border:1px solid {border};" />'
            ).format(url=html.escape(url, quote=True), border=BORDER)
            for url in response[1]
        ]
    )
    return """
<li style="margin-bottom: 12px; list-style: none;">
  <div style="padding: 14px 16px; border-radius: 8px; border: 1px solid {border}; background-color: {card_bg};">
    {name_html}
    {body_html}
    {images}
  </div>
</li>
""".format(
        border=BORDER,
        card_bg=CARD_BG,
        name_html=name_html,
        body_html=body_html,
        images=image_htmls,
    )


def construct_question_text(
    question: str, responses: list[tuple[str, list[str]]]
) -> str:
    """Construct plain text version of a question and its responses.

    Args:
        question: The question text
        responses: List of tuples containing (response text, list of image URLs)

    Returns:
        str: Plain text string containing the question and responses
    """
    return (
        f"{question}:\n"
        + "\n".join([response[0] for response in responses])
        + "\n\n"
    )


def construct_send_letter_email(
    recipients: list[str],
    title: str,
    letter_api_id: str,
    letter_dict: dict[str, list[tuple[str, list[str]]]],
) -> EmailDraft:
    """Construct an email draft containing a complete letter.

    Creates an email draft with all questions and responses from a letter,
    formatted in both HTML and plain text versions. The HTML version includes
    images and proper formatting, while the plain text version serves as a
    fallback for non-HTML email clients.

    Args:
        recipients: List of email addresses to send to
        letter_number: The sequential number of this letter
        group_name: Name of the group
        letter_api_id: API identifier of the letter
        letter_dict: Dictionary mapping questions to lists of responses

    Returns:
        EmailDraft: A draft email ready to be sent
    """
    question_text = "".join(
        construct_question_text(q, r) for q, r in letter_dict.items()
    )

    question_html = "".join(
        construct_question_html(q, r) for q, r in letter_dict.items()
    )

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = question_text

    letter_url = app_url(f"loops/{letter_api_id}")
    content_html = (
        render_button("Read online", letter_url)
        + render_muted_line(
            "Or open this letter in your browser: "
            + f'<a href="{letter_url}" style="color:{MUTED_INK};'
            f'text-decoration:underline;">{letter_url}</a>'
        )
        + question_html
    )

    # The HTML body of the email.
    BODY_HTML = render_email_shell(
        title=title,
        eyebrow="A new letter",
        preheader="A new letter from your group is ready to read.",
        content_html=content_html,
        footer_note="You are receiving this email as a member of a Ring loop.",
    )

    # Try to send the email.
    subject = title
    email_draft = construct_email_draft(
        recipients, subject, BODY_HTML, BODY_TEXT
    )

    return email_draft
