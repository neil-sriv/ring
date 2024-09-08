from __future__ import annotations

from typing import Callable
from sqlalchemy.orm import Session
from ring.email_util import CHARSET, EmailDraft, send_email
from ring.letters.constants import LetterStatus
from ring.tasks.models.task_model import (
    SendEmailTask,
    TaskStatus,
    TaskType,
    Task,
)
from ring.worker.celery_app import CeleryTask, register_task_factory  # type: ignore
from ring.letters.crud import letter as letter_crud


def execute_send_email_task(db: Session, task: SendEmailTask) -> None:
    group = task.schedule.group
    letter_to_send = group.in_progress_letter
    assert letter_to_send
    message_id = send_email(
        construct_send_letter_email(
            [u.email for u in letter_to_send.participants],
            letter_to_send.number,
            group.name,
            letter_to_send.api_identifier,
            letter_crud.compile_letter_dict(letter_to_send),
        )
    )
    if message_id:
        letter_to_send.status = LetterStatus.SENT

    db.commit()


@register_task_factory(name="send_email_task")
def async_send_email_task(self: CeleryTask, task_id: int) -> None:
    task = (
        self.session.query(SendEmailTask)
        .filter(SendEmailTask.id == task_id)
        .one()
    )
    try:
        execute_send_email_task(self.session, task)
    except Exception as e:
        task.status = TaskStatus.FAILED
        task.message = str(e)
    else:
        task.message = ""
        task.status = TaskStatus.COMPLETED
    self.session.commit()


ASYNC_TASK_TO_EXECUTE_MAPPING: dict[TaskType, Callable[..., None]] = {
    TaskType.SEND_EMAIL: async_send_email_task
}


@register_task_factory(name="execute_tasks")
def execute_tasks_async(self: CeleryTask, task_ids: list[int]) -> None:
    execute_tasks(self.session, task_ids)


def execute_tasks(db: Session, task_ids: list[int]) -> None:
    tasks = db.query(Task).filter(Task.id.in_(task_ids)).all()
    for task in tasks:
        task.status = TaskStatus.IN_PROGRESS
    db.commit()
    for task in tasks:
        task_type = TaskType(task.type)
        task_to_execute = ASYNC_TASK_TO_EXECUTE_MAPPING[task_type]
        task_to_execute.delay(task.id)  # type: ignore
    db.commit()


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
    return EmailDraft(
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
