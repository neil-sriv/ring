"""Utilities for constructing waiting-response emails.

These emails notify participants who have not yet answered that a letter
send was deferred because the issue is waiting for their response.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ring.email_util import EmailDraft, construct_email_draft
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

    BODY_HTML = """<html>
    <head></head>
    <body>
    <h1>Ring: {letter_title} is waiting for your response</h1>
    <h2>Check out the issue online at <a href="{letter_url}">{letter_url}</a></h2>
    <p>The latest issue for <strong>{group_name}</strong> has not been sent yet because it is waiting for your response.</p>
    <p>Please visit the link above to add your answers to <strong>{letter_title}</strong>.</p>
    </body>
    </html>
                """.format(
        group_name=group_name,
        letter_url=letter_url,
        letter_title=letter_title,
    )

    subject = "Ring: {} is waiting for your response".format(letter_title)
    return construct_email_draft(recipients, subject, BODY_HTML, BODY_TEXT)
