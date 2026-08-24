"""Utilities for constructing waiting-response emails.

These emails notify participants who have not yet answered that a letter
send was deferred because the issue is waiting for their response.
"""

from __future__ import annotations

import html
from typing import TYPE_CHECKING

from ring.email_template import (
    render_button,
    render_email_shell,
    render_link,
    render_muted_line,
    render_paragraph,
)
from ring.email_util import EmailDraft, construct_email_draft
from ring.lib.app_links import app_url

if TYPE_CHECKING:
    from ring.letters.models.letter_model import Letter
    from ring.parties.models.user_model import User


def letter_non_responder_users(letter: Letter) -> list[User]:
    """Return participants who have not submitted any response."""
    responder_ids = {user.id for user in letter.responders}
    return [
        user for user in letter.participants if user.id not in responder_ids
    ]


def letter_non_responder_emails(letter: Letter) -> list[str]:
    """Return emails of participants who have not submitted any response."""
    return [user.email for user in letter_non_responder_users(letter)]


def letter_display_title(letter: Letter) -> str:
    """Return a human-readable letter title or number for email copy."""
    if letter.title:
        return letter.title
    return f"#{letter.number}"


def construct_waiting_response_email(
    recipients: list[str],
    group_name: str,
    letter_api_id: str,
    letter_title: str,
) -> EmailDraft:
    """Construct an email telling a participant the issue is waiting on them.

    The issue has not been sent yet because too few people have answered.
    This email is sent only to people who have not responded. It does not
    imply a hard last-day deadline; send will be retried later if the
    responder threshold is still unmet.

    Args:
        recipients: Email addresses of participants who have not responded
        group_name: Name of the group
        letter_api_id: API identifier of the letter
        letter_title: Title or number of the letter for display

    Returns:
        EmailDraft: A draft email ready to be sent
    """
    letter_url = app_url(f"loops/{letter_api_id}")

    BODY_TEXT = """The latest Ring issue for {group_name} has not been sent yet because it is waiting for your response.

{letter_title} needs your answers before it can go out to the group.

Visit: {letter_url}
""".format(
        group_name=group_name,
        letter_title=letter_title,
        letter_url=letter_url,
    )

    content_html = (
        render_paragraph(
            "The latest issue for "
            f"<strong>{html.escape(group_name)}</strong> has not been sent "
            "yet because it is waiting for your response."
        )
        + render_button("Add your response", letter_url)
        + render_muted_line(
            "Or open the letter here: " + render_link(letter_url)
        )
    )

    BODY_HTML = render_email_shell(
        title=f"{letter_title} is waiting on you",
        eyebrow=group_name,
        preheader=(
            f"{letter_title} has not been sent yet — it is waiting for your "
            "response."
        ),
        content_html=content_html,
        footer_note="You are receiving this email as a member of a Ring loop.",
    )

    subject = "Ring: {} is waiting for your response".format(letter_title)
    return construct_email_draft(recipients, subject, BODY_HTML, BODY_TEXT)
