"""Utilities for constructing reminder email tasks.

This module provides functions for creating email drafts for reminder emails,
which notify users about upcoming deadlines for adding questions or responding
to letters in Ring.
"""

from __future__ import annotations

import html
from datetime import datetime

from ring.email_template import (
    render_button,
    render_email_shell,
    render_link,
    render_muted_line,
    render_paragraph,
)
from ring.email_util import EmailDraft, construct_email_draft
from ring.letters.constants import LetterStatus
from ring.letters.time_left import days_left_to, reminder_deadline
from ring.lib.app_links import app_url


def construct_reminder_email(
    recipients: list[str],
    group_name: str,
    letter_api_id: str,
    letter_status: str,
    send_at: datetime,
    letter_type: str,
    *,
    now: datetime | None = None,
) -> EmailDraft:
    """Construct a reminder email draft.

    Creates an email draft reminding users to either add questions or respond
    to a letter, depending on the letter's status. The email includes both
    plain text and HTML versions.

    Args:
        recipients: List of email addresses to send to
        group_name: Name of the group
        letter_api_id: API identifier of the letter
        letter_status: Status of the letter (UPCOMING or IN_PROGRESS)
        send_at: When the letter is scheduled to send
        letter_type: Type of the letter (CYCLIC or ADHOC)
        now: Clock for the day count. Defaults to the current time.

    Returns:
        EmailDraft: A draft email ready to be sent
    """
    subject_text = (
        "add questions"
        if letter_status == LetterStatus.UPCOMING
        else "respond"
    )
    lead = days_left_to(
        subject_text,
        reminder_deadline(send_at, letter_status, letter_type),
        now,
    )

    letter_url = app_url(f"loops/{letter_api_id}")
    BODY_TEXT = f"{lead} for the newsletter.\n\nVisit: {letter_url}"
    cta_label = (
        "Add questions"
        if letter_status == LetterStatus.UPCOMING
        else "Write your response"
    )
    content_html = (
        render_paragraph(
            f"{html.escape(lead)} for the latest "
            f"<strong>{html.escape(group_name)}</strong> letter."
        )
        + render_button(cta_label, letter_url)
        + render_muted_line(
            "Or open the letter here: " + render_link(letter_url)
        )
    )

    # The HTML body of the email.
    BODY_HTML = render_email_shell(
        title=lead,
        eyebrow=group_name,
        preheader=f"{lead} for {group_name}.",
        content_html=content_html,
        footer_note="You are receiving this email as a member of a Ring loop.",
    )

    subject = f"Ring Reminder: {lead} for {group_name}"
    email_draft = construct_email_draft(
        recipients, subject, BODY_HTML, BODY_TEXT
    )

    return email_draft
