"""CRUD operations for default question management.

This module provides functions for managing default questions that are automatically
added to new letters in a group, including adding, retrieving, and replacing questions.
"""

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

    Args:
        db (Session): Database session
        group (Group): Group to add the default question to
        question_text (str): Text content of the default question

    Returns:
        DefaultQuestion: Newly created default question
    """
    dfq = DefaultQuestion.create(question_text=question_text, group=group)
    db.add(dfq)
    return dfq


def get_default_questions(
    db: Session, group: Group
) -> Sequence[DefaultQuestion]:
    """Retrieve all default questions for a group.

    Args:
        db (Session): Database session
        group (Group): Group to get default questions for

    Returns:
        Sequence[DefaultQuestion]: List of default questions
    """
    return db.scalars(
        sqlalchemy.select(DefaultQuestion).where(
            DefaultQuestion.group == group
        )
    ).all()


def delete_default_question(db: Session, api_id: str) -> None:
    """Delete a default question by its API identifier.

    Args:
        db (Session): Database session
        api_id (str): API identifier of the default question to delete

    Raises:
        IDNotFoundException: If default question with given API ID is not found
    """
    dfq = get_model(db, DefaultQuestion, api_id)
    db.delete(dfq)


def replace_default_questions(
    db: Session, group: Group, questions: Sequence[str]
) -> None:
    """Replace all default questions for a group with a new set.

    Args:
        db (Session): Database session
        group (Group): Group to update default questions for
        questions (Sequence[str]): New sequence of question texts
    """
    group.default_questions.clear()
    for question in questions:
        add_default_question(db, group, question)
