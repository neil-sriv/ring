"""Utilities for constructing response open email tasks.

This module provides functions for creating email drafts for notifying users
when a recurring newsletter becomes open for responses (when it's promoted
from UPCOMING to IN_PROGRESS status).
"""

from __future__ import annotations

import html

from ring.email_template import (
    render_button,
    render_email_shell,
    render_link,
    render_muted_line,
    render_paragraph,
)
from ring.email_util import EmailDraft, construct_email_draft
from ring.lib.app_links import app_url


def construct_response_open_email(
    recipients: list[str],
    group_name: str,
    letter_api_id: str,
    letter_title: str,
) -> EmailDraft:
    """Construct an email notifying users that a newsletter is open for responses.

    Creates an email draft informing users that the newsletter has moved from
    the question-adding phase to the response phase. The email includes both
    plain text and HTML versions.

    Args:
        recipients: List of email addresses to send to
        group_name: Name of the group
        letter_api_id: API identifier of the letter
        letter_title: Title or number of the letter for display

    Returns:
        EmailDraft: A draft email ready to be sent
    """
    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = """Ring Newsletter for {group_name} is now open for responses!

The newsletter {letter_title} is now ready for your responses. Head over to Ring to share your answers to this week's questions.

Visit: {letter_url}
""".format(
        group_name=group_name,
        letter_title=letter_title,
        letter_url=app_url(f"loops/{letter_api_id}"),
    )

    letter_url = app_url(f"loops/{letter_api_id}")
    content_html = (
        render_paragraph(
            f"<strong>{html.escape(letter_title)}</strong> is ready for your "
            "answers. Head over to Ring to respond to this issue's questions."
        )
        + render_button("Write your answers", letter_url)
        + render_muted_line(
            "Or open the letter here: " + render_link(letter_url)
        )
    )

    # The HTML body of the email.
    BODY_HTML = render_email_shell(
        title=f"{letter_title} is open for responses",
        eyebrow=group_name,
        preheader=f"{letter_title} is now ready for your answers.",
        content_html=content_html,
        footer_note="You are receiving this email as a member of a Ring loop.",
    )

    subject = "Ring: {} is now open for responses!".format(letter_title)
    email_draft = construct_email_draft(
        recipients, subject, BODY_HTML, BODY_TEXT
    )

    return email_draft
