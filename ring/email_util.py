"""Email utilities for Ring using AWS SES.

This module provides utilities for constructing and sending emails through AWS SES.
It uses a functional approach with immutable data structures (dataclasses) for
email drafts and provides type-safe interfaces for email operations.
"""

from dataclasses import dataclass
from typing import Optional

import boto3
from mypy_boto3_ses.client import BotocoreClientError, SESClient
from mypy_boto3_ses.type_defs import (
    DestinationTypeDef,
    MessageTypeDef,
)

# The character encoding for the email.
CHARSET = "UTF-8"


@dataclass
class EmailDraft:
    """Immutable representation of an email to be sent via AWS SES.

    This class uses the RORO (Receive an Object, Return an Object) pattern
    to encapsulate email data in a type-safe way.

    Attributes:
        destination: AWS SES destination configuration (To, CC, BCC addresses)
        message: AWS SES message configuration (subject and body content)
        source: Sender email address (defaults to Ring system email)
    """
    destination: DestinationTypeDef
    message: MessageTypeDef
    source: str = "ring@neilsriv.tech"


def construct_email_draft(
    recipients: list[str],
    subject: str,
    body_html: str,
    body_text: str | None = None,
) -> EmailDraft:
    """Construct an email draft with both HTML and plain text content.

    This function follows functional programming principles by creating an
    immutable EmailDraft object without side effects.

    Args:
        recipients: List of recipient email addresses
        subject: Email subject line
        body_html: HTML version of the email body
        body_text: Optional plain text version (defaults to HTML content)

    Returns:
        EmailDraft: A configured email draft ready to be sent

    Example:
        ```python
        draft = construct_email_draft(
            recipients=["user@example.com"],
            subject="Welcome to Ring",
            body_html="<h1>Welcome!</h1>",
        )
        ```
    """
    if not body_text:
        body_text = body_html
    return EmailDraft(
        destination={"ToAddresses": recipients},
        message={
            "Subject": {
                "Data": subject,
                "Charset": CHARSET,
            },
            "Body": {
                "Text": {
                    "Data": body_text,
                    "Charset": CHARSET,
                },
                "Html": {
                    "Data": body_html,
                    "Charset": CHARSET,
                },
            },
        },
    )


def send_email(draft: EmailDraft) -> Optional[str]:
    """Send an email using AWS SES.

    This function handles the actual sending of the email through AWS SES,
    with proper error handling and logging.

    Args:
        draft: The email draft to send

    Returns:
        Optional[str]: The AWS SES message ID if successful, None if sending failed

    Example:
        ```python
        draft = construct_email_draft(...)
        if message_id := send_email(draft):
            print(f"Email sent successfully with ID: {message_id}")
        else:
            print("Failed to send email")
        ```
    """
    ses_client: SESClient = boto3.Session().client(
        "ses", region_name="us-east-1"
    )  # type: ignore
    try:
        response = ses_client.send_email(
            Source=draft.source,
            Destination=draft.destination,
            Message=draft.message,
        )
    except BotocoreClientError as e:
        print(e.response["Error"]["Message"])
        return None
    else:
        print(f"Email sent! Message ID: {response['MessageId']}")
        return response["MessageId"]
