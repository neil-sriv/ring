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
    destination: DestinationTypeDef
    message: MessageTypeDef
    source: str = "ring@neilsriv.tech"


def construct_email_draft(
    recipients: list[str],
    subject: str,
    body_html: str,
    body_text: str | None = None,
) -> EmailDraft:
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
