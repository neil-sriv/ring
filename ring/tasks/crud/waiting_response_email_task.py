"""Utilities for constructing waiting-response emails.

These emails notify participants who have not yet answered that a letter
send was deferred because the issue is waiting for their response.
"""

from __future__ import annotations

import html
from datetime import datetime
from typing import TYPE_CHECKING

from ring.email_template import (
    render_button,
    render_email_shell,
    render_link,
    render_muted_line,
    render_paragraph,
)
from ring.email_util import EmailDraft, construct_email_draft
from ring.letters.time_left import days_left_label
from ring.lib.app_links import app_url

if TYPE_CHECKING:
    from ring.letters.models.letter_model import Letter


def letter_non_responder_emails(letter: Letter) -> list[str]:
    """Return emails of participants who have not submitted any response."""
    responder_ids = {user.id for user in letter.responders}
    return [
        user.email
        for user in letter.participants
        if user.id not in responder_ids
    ]


def letter_display_title(letter: Letter) -> str:
    """Return a human-readable letter title or number for email copy."""
    if letter.title:
        return letter.title
    return f"#{letter.number}"


def _response_countdown(label: str) -> str:
    """Days left to respond. A passed send time says due today."""
    if label == "today":
        return "Due today"
    if label == "less than a day":
        return "Less than a day left to respond"
    return f"{label} left to respond"


def construct_waiting_response_email(
    recipients: list[str],
    group_name: str,
    letter_api_id: str,
    letter_title: str,
    send_at: datetime,
    *,
    now: datetime | None = None,
) -> EmailDraft:
    """Construct an email telling a participant the issue is waiting on them.

    The issue has not been sent yet because too few people have answered.
    This email is sent only to people who have not responded. It names the
    days left until the current send time. It does not imply a hard
    last-day deadline; send will be retried later if the responder
    threshold is still unmet.

    Args:
        recipients: Email addresses of participants who have not responded
        group_name: Name of the group
        letter_api_id: API identifier of the letter
        letter_title: Title or number of the letter for display
        send_at: When the letter is scheduled to send
        now: Clock for the day count. Defaults to the current time.

    Returns:
        EmailDraft: A draft email ready to be sent
    """
    letter_url = app_url(f"loops/{letter_api_id}")
    label = days_left_label(send_at, now)
    countdown = _response_countdown(label)
    short = "due today" if label == "today" else f"{label} left"

    BODY_TEXT = """The latest Ring issue for {group_name} has not been sent yet because it is waiting for your response.

{countdown}.

{letter_title} needs your answers before it can go out to the group.

Visit: {letter_url}
""".format(
        group_name=group_name,
        countdown=countdown,
        letter_title=letter_title,
        letter_url=letter_url,
    )

    content_html = (
        render_paragraph(
            "The latest issue for "
            f"<strong>{html.escape(group_name)}</strong> has not been sent "
            "yet because it is waiting for your response."
        )
        + render_paragraph(f"{html.escape(countdown)}.")
        + render_button("Add your response", letter_url)
        + render_muted_line(
            "Or open the letter here: " + render_link(letter_url)
        )
    )

    BODY_HTML = render_email_shell(
        title=f"{letter_title} is waiting on you",
        eyebrow=group_name,
        preheader=f"{letter_title} has not been sent yet. {countdown}.",
        content_html=content_html,
        footer_note="You are receiving this email as a member of a Ring loop.",
    )

    subject = f"Ring: {letter_title} is waiting for your response — {short}"
    return construct_email_draft(recipients, subject, BODY_HTML, BODY_TEXT)
