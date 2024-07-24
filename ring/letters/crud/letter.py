from __future__ import annotations
from datetime import datetime
from typing import TYPE_CHECKING, Sequence

from sqlalchemy import select
from ring.api_identifier import util as api_identifier_crud
from ring.letters.models.letter_model import Letter
from ring.parties.models.group_model import Group
from ring.tasks.crud import schedule as schedule_crud
from ring.letters.constants import LetterStatus
from ring.letters.models.question_model import Question
from ring.tasks.models.task_model import TaskType
from ring.parties.models.user_model import User

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_letters(
    db: Session, group_api_id: str, skip: int = 0, limit: int = 100
) -> Sequence[Letter]:
    group = api_identifier_crud.get_model(db, Group, api_id=group_api_id)
    return db.scalars(
        select(Letter).filter(Letter.group == group).offset(skip).limit(limit)
    ).all()


def create_letter(
    db: Session,
    group_api_id: str,
    send_at: datetime,
    number: int | None = None,
    letter_status: LetterStatus = LetterStatus.IN_PROGRESS,
) -> Letter:
    group = api_identifier_crud.get_model(
        db,
        Group,
        api_id=group_api_id,
    )
    db_letter = Letter.create(group, send_at, letter_status, number=number)
    db.add(db_letter)

    if letter_status == LetterStatus.IN_PROGRESS:
        schedule_crud.register_task(
            db,
            db_letter.group.schedule,
            TaskType.SEND_EMAIL,
            send_at,
            {},
        )
    return db_letter


def add_question(
    db: Session, letter: Letter, question_text: str, author: User | None = None
) -> Question:
    question = Question.create(letter, question_text, author)
    db.add(question)
    letter.questions.append(question)
    return question


def compile_letter_dict(letter: Letter) -> dict[str, list[str]]:
    return {
        q.question_text: [
            f"{resp.participant.name}: {resp.response_text}" for resp in q.responses
        ]
        for q in letter.questions
    }