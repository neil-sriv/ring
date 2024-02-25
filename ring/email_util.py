from mypy_boto3_ses.client import SESClient
from mypy_boto3_ses.type_defs import (
    DestinationTypeDef,
    MessageTypeDef,
)
from dataclasses import dataclass
import boto3


@dataclass
class EmailDraft:
    source: str
    destination: DestinationTypeDef
    message: MessageTypeDef


def send_email(draft: EmailDraft) -> None:
    ses_client: SESClient = boto3.Session().client("ses")  # type: ignore
    ses_client.send_email(
        Source=draft.source,
        Destination=draft.destination,
        Message=draft.message,
    )


def construct_email() -> EmailDraft:
    return EmailDraft(
        source="",
        destination={"ToAddresses": []},
        message={
            "Subject": {"Data": "Your daily schedule"},
            "Body": {
                "Text": {
                    "Data": "You have a new schedule for today. Please check your account."
                }
            },
        },
    )
