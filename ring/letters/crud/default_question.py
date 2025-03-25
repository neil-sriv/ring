from typing import Sequence

import sqlalchemy
from sqlalchemy.orm import Session

from ring.api_identifier.util import get_model
from ring.letters.models.default_question_model import DefaultQuestion
from ring.parties.models.group_model import Group


def add_default_question(
    db: Session, group: Group, question_text: str
) -> DefaultQuestion:
    """Add a new default question to a group.

    :param db: Database session
    :param group: Group to add the default question to
    :param question_text: Text content of the default question
    :return: Newly created default question
    :rtype: DefaultQuestion
    """
    dfq = DefaultQuestion.create(question_text=question_text, group=group)
    db.add(dfq)
    return dfq


def get_default_questions(
    db: Session, group: Group
) -> Sequence[DefaultQuestion]:
    """Retrieve all default questions for a group.

    :param db: Database session
    :param group: Group to get default questions for
    :return: Sequence of default questions
    :rtype: Sequence[DefaultQuestion]
    """
    return db.scalars(
        sqlalchemy.select(DefaultQuestion).where(
            DefaultQuestion.group == group
        )
    ).all()


def delete_default_question(db: Session, api_id: str) -> None:
    """Delete a default question by its API identifier.

    :param db: Database session
    :param api_id: API identifier of the default question to delete
    :raises IDNotFoundException: If default question with given API ID is not found
    """
    dfq = get_model(db, DefaultQuestion, api_id)
    db.delete(dfq)


def replace_default_questions(
    db: Session, group: Group, questions: Sequence[str]
) -> None:
    """Replace all default questions for a group with a new set.

    :param db: Database session
    :param group: Group to update default questions for
    :param questions: New sequence of question texts
    """
    group.default_questions.clear()
    for question in questions:
        add_default_question(db, group, question)
