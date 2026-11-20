"""Batched email for questions added to an in-progress letter.

One email lists every late question added since the last such email.
The copy stays plain: question text and who asked, with no Late badge.
"""

from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import UTC, datetime

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from ring.email_template import (
    render_button,
    render_email_shell,
    render_link,
    render_muted_line,
    render_paragraph,
)
from ring.email_util import EmailDraft, construct_email_draft, send_email
from ring.letters.constants import LetterStatus
from ring.letters.crud.letter import (
    late_question_cutoff_reached,
    late_question_recipients,
)
from ring.letters.models.late_question_email_receipt import (
    LateQuestionEmailReceipt,
)
from ring.letters.models.letter_model import Letter
from ring.letters.models.question_model import Question
from ring.lib.app_links import app_url
from ring.parties.models.user_model import User
from ring.tasks.crud.waiting_response_email_task import letter_display_title


def unsent_late_questions(letter: Letter, as_of: datetime) -> list[Question]:
    """Late questions created after the last email and no later than ``as_of``.

    Deleted questions are already gone, so they cannot appear. A letter
    that has never sent this email includes every remaining late question
    created by ``as_of``. A question created after ``as_of`` stays eligible
    for the next email.
    """
    watermark = letter.last_late_question_email_at
    questions = [
        question
        for question in letter.questions
        if question.added_late
        and question.created_at <= as_of
        and (watermark is None or question.created_at > watermark)
    ]
    questions.sort(key=lambda question: (question.position, question.id))
    return questions


@dataclass(frozen=True)
class LateQuestionEmailResult:
    """What the sender should do with the task after this attempt.

    ``retry`` is set only when the provider rejected a batch that still
    has recipients. A drop, an empty batch, or a fully accepted send
    leaves it false.
    """

    retry: bool
    sent_any: bool


def _already_sent(
    db: Session, letter: Letter, questions: list[Question]
) -> set[tuple[int, int]]:
    """Return ``(user_id, question_id)`` pairs already emailed."""
    if not questions:
        return set()
    rows = db.execute(
        select(
            LateQuestionEmailReceipt.user_id,
            LateQuestionEmailReceipt.question_id,
        ).where(
            LateQuestionEmailReceipt.letter_id == letter.id,
            LateQuestionEmailReceipt.question_id.in_(
                [question.id for question in questions]
            ),
        )
    ).all()
    return {(row.user_id, row.question_id) for row in rows}


def _record_receipts(
    db: Session,
    letter: Letter,
    users: list[User],
    questions: list[Question],
) -> None:
    """Remember a provider-accepted batch so a retry will not resend it."""
    for user in users:
        for question in questions:
            db.add(
                LateQuestionEmailReceipt(
                    letter_id=letter.id,
                    user_id=user.id,
                    question_id=question.id,
                )
            )
    db.commit()


def late_question_email_batches(
    letter: Letter,
    questions: list[Question],
    already_sent: set[tuple[int, int]] | None = None,
) -> list[tuple[list[User], list[Question]]]:
    """Group responders by the questions they still need to be emailed.

    Each batch is one email. Recipients are ``late_question_recipients``
    for the questions in the batch, so a person who has not responded is
    left out and an author is left off the questions they asked. Pairs in
    ``already_sent`` were accepted on an earlier attempt and are skipped.
    """
    sent = already_sent or set()
    questions_for_user: dict[int, list[Question]] = {}
    users: dict[int, User] = {}
    for question in questions:
        for user in late_question_recipients(letter, question.author):
            if (user.id, question.id) in sent:
                continue
            users[user.id] = user
            questions_for_user.setdefault(user.id, []).append(question)
    batches: dict[tuple[int, ...], list[User]] = {}
    order: list[tuple[int, ...]] = []
    for user_id, visible in questions_for_user.items():
        key = tuple(question.id for question in visible)
        if key not in batches:
            order.append(key)
            batches[key] = []
        batches[key].append(users[user_id])
    question_by_id = {question.id: question for question in questions}
    return [
        (
            batches[key],
            [question_by_id[question_id] for question_id in key],
        )
        for key in order
    ]


def _author_name(question: Question) -> str:
    if question.author is not None:
        return question.author.name
    return "Someone"


def _question_lines(questions: list[Question]) -> list[str]:
    authors = {_author_name(question) for question in questions}
    if len(questions) > 1 and len(authors) > 1:
        return [
            f"{_author_name(question)}: {question.question_text}"
            for question in questions
        ]
    return [question.question_text for question in questions]


def _intro(
    letter_title: str, group_name: str, questions: list[Question]
) -> str:
    authors = {_author_name(question) for question in questions}
    if len(authors) == 1:
        author = next(iter(authors))
        noun = "a question" if len(questions) == 1 else "questions"
        return f"{author} added {noun} to {letter_title} in {group_name}."
    return f"New questions were added to {letter_title} in {group_name}."


def construct_late_question_email(
    recipients: list[str],
    group_name: str,
    letter_api_id: str,
    letter_title: str,
    questions: list[Question],
) -> EmailDraft:
    """Build the plain late-question email for one recipient batch.

    The subject and body name the questions and who asked them. They do
    not include a Late badge.
    """
    letter_url = app_url(f"loops/{letter_api_id}")
    intro = _intro(letter_title, group_name, questions)
    lines = _question_lines(questions)
    subject_noun = "question" if len(questions) == 1 else "questions"
    subject = f"Ring: New {subject_noun} on {letter_title}"
    text_questions = "\n".join(lines)
    body_text = f"{intro}\n\n{text_questions}\n\nVisit: {letter_url}\n"
    content_html = render_paragraph(html.escape(intro))
    for line in lines:
        content_html += render_paragraph(html.escape(line))
    content_html += render_button("Open the loop", letter_url)
    content_html += render_muted_line(
        "Or open the letter here: " + render_link(letter_url)
    )
    body_html = render_email_shell(
        title=f"New {subject_noun} on {letter_title}",
        eyebrow=group_name,
        preheader=intro,
        content_html=content_html,
        footer_note=(
            "You are receiving this email as a member of a Ring loop."
        ),
    )
    return construct_email_draft(recipients, subject, body_html, body_text)


def _advance_watermark(letter: Letter, as_of: datetime) -> None:
    letter.last_late_question_email_at = as_of


def deliver_late_question_email(
    db: Session, letter: Letter
) -> LateQuestionEmailResult:
    """Send the batched email, or drop it.

    Sends nothing once the letter is sent or inside the 24h cutoff, when
    no late questions remain, or when nobody who already replied is left
    after excluding authors. Each accepted batch is recorded per
    recipient and question before the next batch is attempted. A rejected
    batch asks the caller to retry; people already recorded are left out
    of that retry. The watermark moves only when every remaining batch
    has been accepted. It is the time this send started, so a question
    created while it runs stays eligible for the next email.

    Returns:
        LateQuestionEmailResult: Whether to retry, and whether any email
        was accepted on this attempt.
    """
    if letter.status != LetterStatus.IN_PROGRESS:
        logger.info(
            "Skipping late-question email for letter {}: status is {}".format(
                letter.id, letter.status
            )
        )
        return LateQuestionEmailResult(retry=False, sent_any=False)
    if late_question_cutoff_reached(letter):
        logger.info(
            "Skipping late-question email for letter {}: "
            "within 24h of send_at {}".format(letter.id, letter.send_at)
        )
        return LateQuestionEmailResult(retry=False, sent_any=False)
    as_of = datetime.now(tz=UTC)
    questions = unsent_late_questions(letter, as_of)
    if not questions:
        logger.info(
            "No late questions left to email for letter {}".format(letter.id)
        )
        return LateQuestionEmailResult(retry=False, sent_any=False)
    already_sent = _already_sent(db, letter, questions)
    batches = late_question_email_batches(
        letter, questions, already_sent=already_sent
    )
    if not batches:
        logger.info(
            "Late-question email for letter {} was already delivered".format(
                letter.id
            )
        )
        _advance_watermark(letter, as_of)
        db.flush()
        return LateQuestionEmailResult(retry=False, sent_any=False)

    letter_title = letter_display_title(letter)
    sent_any = False
    for users, visible in batches:
        recipients = [user.email for user in users]
        message_id = send_email(
            construct_late_question_email(
                recipients,
                letter.group.name,
                letter.api_identifier,
                letter_title,
                visible,
            )
        )
        if not message_id:
            logger.warning(
                "Late-question email for letter {} was not accepted; "
                "retrying the recipients who have not received it".format(
                    letter.id
                )
            )
            return LateQuestionEmailResult(retry=True, sent_any=sent_any)
        _record_receipts(db, letter, users, visible)
        sent_any = True
        logger.info(
            "Sent late-question email for letter {} to {}".format(
                letter.id, recipients
            )
        )
    _advance_watermark(letter, as_of)
    db.flush()
    return LateQuestionEmailResult(retry=False, sent_any=sent_any)
