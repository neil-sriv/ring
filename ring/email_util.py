from typing import Optional
from mypy_boto3_ses.client import SESClient, BotocoreClientError
from mypy_boto3_ses.type_defs import (
    DestinationTypeDef,
    MessageTypeDef,
)
from dataclasses import dataclass
import boto3


# The character encoding for the email.
CHARSET = "UTF-8"


@dataclass
class EmailDraft:
    destination: DestinationTypeDef
    message: MessageTypeDef
    source: str = "ring@neilsriv.tech"


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
