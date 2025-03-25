"""Utilities for constructing reminder email tasks.

This module provides functions for creating email drafts for reminder emails,
which notify users about upcoming deadlines for adding questions or responding
to letters in Ring.
"""

from ring.email_util import EmailDraft, construct_email_draft
from ring.letters.constants import LetterStatus


def construct_reminder_email(
    recipients: list[str],
    group_name: str,
    letter_api_id: str,
    letter_status: str,
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

    Returns:
        EmailDraft: A draft email ready to be sent
    """
    subject_text = (
        "add questions"
        if letter_status == LetterStatus.UPCOMING
        else "respond"
    )

    question_text = "Today is the last day to {} for the newsletter. Please visit the link above to {}.".format(
        subject_text,
        subject_text,
    )

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = question_text

    # The HTML body of the email.
    BODY_HTML = """<html>
    <head></head>
    <body>
    <h1>Ring Reminder: Last day to {subject_text} for {group_name}</h1>
    <h2>Check out the newsletter online at <a href="http://ring.neilsriv.tech/loops/{letter_api_id}">http://ring.neilsriv.tech</a></h2>
    <p>Today is the last day to {subject_text} for the newsletter. Please visit the link above to {subject_text}.</p>
    </body>
    </html>
                """.format(
        subject_text=subject_text,
        group_name=group_name,
        letter_api_id=letter_api_id,
    )

    # Try to send the email.
    subject = "Ring Reminder: Last day to {} for {}".format(
        subject_text,
        group_name,
    )
    email_draft = construct_email_draft(
        recipients, subject, BODY_HTML, BODY_TEXT
    )

    return email_draft
