from typing import Optional
from mypy_boto3_ses.client import SESClient, BotocoreClientError
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


def send_email(draft: EmailDraft) -> Optional[str]:
    ses_client: SESClient = boto3.Session().client("ses", region_name="us-east-1")  # type: ignore
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


def construct_question_html(
    question: str, responses: list[tuple[str, list[str]]]
) -> str:
    return f"""
    <h2>{question}</h2>
    <ul>
        {"".join([construct_response_html(response) for response in responses])}
    </ul>
"""


def construct_response_html(response: tuple[str, list[str]]) -> str:
    image_htmls = "".join(
        [
            f'<img src="{url}" alt="Image" style="display:block" width="200" height="400" />'
            for url in response[1]
        ]
    )
    return f"""<li>
<p>{response[0]}</p>
{image_htmls}
</li>"""


def construct_question_text(
    question: str, responses: list[tuple[str, list[str]]]
) -> str:
    return (
        f"{question}:\n" + "\n".join([response[0] for response in responses]) + "\n\n"
    )


def construct_html_email(
    recipients: list[str],
    letter_number: int,
    group_name: str,
    letter_api_id: str,
    letter_dict: dict[str, list[tuple[str, list[str]]]],
) -> EmailDraft:
    question_text = "".join(
        construct_question_text(q, r) for q, r in letter_dict.items()
    )

    question_html = "".join(
        construct_question_html(q, r) for q, r in letter_dict.items()
    )

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = question_text

    # The HTML body of the email.
    BODY_HTML = """<html>
    <head></head>
    <body>
    <h1>Ring Newsletter #{letter_number} for {group_name}</h1>
    <h2>Check out the newsletter online at <a href="http://ring.neilsriv.tech/loops/{letter_api_id}">ring.neilsriv.tech</a></h2>
    {question_html}
    </body>
    </html>
                """.format(
        letter_number=letter_number,
        group_name=group_name,
        letter_api_id=letter_api_id,
        question_html=question_html,
    )

    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Try to send the email.
    return EmailDraft(
        source="ring@neilsriv.tech",
        destination={"ToAddresses": recipients},
        message={
            "Subject": {
                "Data": "Ring: Newsletter #{} for {}".format(
                    letter_number,
                    group_name,
                ),
                "Charset": CHARSET,
            },
            "Body": {
                "Text": {
                    "Data": BODY_TEXT,
                    "Charset": CHARSET,
                },
                "Html": {
                    "Data": BODY_HTML,
                    "Charset": CHARSET,
                },
            },
        },
    )
