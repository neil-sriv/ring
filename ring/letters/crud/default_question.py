from typing import Sequence
import sqlalchemy
from ring.api_identifier.util import get_model
from ring.letters.models.default_question_model import DefaultQuestion
from ring.parties.models.group_model import Group
from sqlalchemy.orm import Session


def add_default_question(
    db: Session, group: Group, question_text: str
) -> DefaultQuestion:
    dfq = DefaultQuestion.create(question_text=question_text, group=group)
    db.add(dfq)
    return dfq


def get_default_questions(
    db: Session, group: Group
) -> Sequence[DefaultQuestion]:
    return db.scalars(
        sqlalchemy.select(DefaultQuestion).where(
            DefaultQuestion.group == group
        )
    ).all()


def delete_default_question(db: Session, api_id: str) -> None:
    dfq = get_model(db, DefaultQuestion, api_id)
    db.delete(dfq)


def replace_default_questions(
    db: Session, group: Group, questions: Sequence[str]
) -> None:
    group.default_questions.clear()
    for question in questions:
        add_default_question(db, group, question)
