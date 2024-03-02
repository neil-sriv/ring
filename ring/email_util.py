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


def construct_email(
    recipients: list[str],
    letter_number: int,
    group_name: str,
    letter_dict: dict[str, list[str]],
) -> EmailDraft:
    def construct_question_text(question: str, responses: list[str]) -> str:
        return f"{question}:\n" + "\n".join(responses) + "\n\n"

    question_text = "".join(
        construct_question_text(q, r) for q, r in letter_dict.items()
    )

    return EmailDraft(
        source="",
        destination={"ToAddresses": recipients},
        message={
            "Subject": {
                "Data": "Ring: Newsletter #{} for {}".format(
                    letter_number,
                    group_name,
                )
            },
            "Body": {"Text": {"Data": question_text}},
        },
    )
