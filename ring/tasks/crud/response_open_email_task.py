"""Utilities for constructing response open email tasks.

This module provides functions for creating email drafts for notifying users
when a recurring newsletter becomes open for responses (when it's promoted
from UPCOMING to IN_PROGRESS status).
"""

from __future__ import annotations

from ring.email_util import EmailDraft, construct_email_draft


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

Visit: http://ring.neilsriv.tech/loops/{letter_api_id}
""".format(
        group_name=group_name,
        letter_title=letter_title,
        letter_api_id=letter_api_id,
    )

    # The HTML body of the email.
    BODY_HTML = """<html>
    <head></head>
    <body>
    <h1>Ring Newsletter for {group_name} is now open for responses!</h1>
    <h2>Check out the newsletter online at <a href="http://ring.neilsriv.tech/loops/{letter_api_id}">http://ring.neilsriv.tech</a></h2>
    <p>The newsletter <strong>{letter_title}</strong> is now ready for your responses.</p>
    <p>Head over to Ring to share your answers to this week's questions!</p>
    </body>
    </html>
                """.format(
        group_name=group_name,
        letter_api_id=letter_api_id,
        letter_title=letter_title,
    )

    subject = "Ring: {} is now open for responses!".format(letter_title)
    email_draft = construct_email_draft(
        recipients, subject, BODY_HTML, BODY_TEXT
    )

    return email_draft
