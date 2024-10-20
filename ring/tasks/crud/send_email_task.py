from ring.email_util import EmailDraft, construct_email_draft


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
            f'<img src="{url}" alt="Image" style="display:block; width:auto; height:auto; max-width:50%;"/>'
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
        f"{question}:\n"
        + "\n".join([response[0] for response in responses])
        + "\n\n"
    )


def construct_send_letter_email(
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
    <h2>Check out the newsletter online at <a href="http://ring.neilsriv.tech/loops/{letter_api_id}">http://ring.neilsriv.tech</a></h2>
    {question_html}
    </body>
    </html>
                """.format(
        letter_number=letter_number,
        group_name=group_name,
        letter_api_id=letter_api_id,
        question_html=question_html,
    )

    # Try to send the email.
    subject = "Ring: Newsletter #{} for {}".format(
        letter_number,
        group_name,
    )
    email_draft = construct_email_draft(
        recipients, subject, BODY_HTML, BODY_TEXT
    )

    return email_draft
