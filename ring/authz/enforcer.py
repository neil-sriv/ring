from __future__ import annotations

from enum import Enum

from casbin import Enforcer, Model
from sqlalchemy import select
from sqlalchemy.orm import Session

from ring.letters.models.letter_model import Letter
from ring.letters.models.question_model import Question
from ring.letters.models.response_model import Response
from ring.parties.models.group_model import Group
from ring.parties.models.user_model import User


class Action(Enum):
    """Action to perform on a resource."""

    READ = "read"
    WRITE = "write"


def get_enforcer() -> Enforcer:
    """Get the enforcer for the authz system."""
    model = Model()
    model.load_model("/src/ring/authz/model.conf")
    return Enforcer(model=model, adapter=None)


def build_stateless_enforcer(db: Session, sub_api_id: str) -> Enforcer:
    """Build a stateless enforcer for a request.

    Loads grouping and permission policies with separate queries (no
    letters × members × questions × responses cartesian join) and
    deduplicates before inserting into Casbin.
    """
    enforcer = get_enforcer()

    group_api_ids = list(
        db.execute(
            select(Group.api_identifier)
            .join(Group.members)
            .where(User.api_identifier == sub_api_id)
        )
        .scalars()
        .all()
    )
    if not group_api_ids:
        return enforcer

    # g + g2: every member of the subject's groups
    member_pairs = {
        (user_api_id, group_api_id)
        for user_api_id, group_api_id in db.execute(
            select(User.api_identifier, Group.api_identifier)
            .join(Group.members)
            .where(Group.api_identifier.in_(group_api_ids))
        ).all()
    }
    for user_api_id, group_api_id in member_pairs:
        enforcer.add_grouping_policy(user_api_id, group_api_id)
        enforcer.add_named_grouping_policy("g2", user_api_id, group_api_id)

    # g2: letter -> group
    letter_pairs = {
        (letter_api_id, group_api_id)
        for letter_api_id, group_api_id in db.execute(
            select(Letter.api_identifier, Group.api_identifier)
            .join(Letter.group)
            .where(Group.api_identifier.in_(group_api_ids))
        ).all()
    }
    for letter_api_id, group_api_id in letter_pairs:
        enforcer.add_named_grouping_policy("g2", letter_api_id, group_api_id)

    # g2: question -> letter
    question_pairs = {
        (question_api_id, letter_api_id)
        for question_api_id, letter_api_id in db.execute(
            select(Question.api_identifier, Letter.api_identifier)
            .join(Question.letter)
            .join(Letter.group)
            .where(Group.api_identifier.in_(group_api_ids))
        ).all()
    }
    for question_api_id, letter_api_id in question_pairs:
        enforcer.add_named_grouping_policy(
            "g2", question_api_id, letter_api_id
        )

    # g2: response -> question
    response_pairs = {
        (response_api_id, question_api_id)
        for response_api_id, question_api_id in db.execute(
            select(Response.api_identifier, Question.api_identifier)
            .join(Response.question)
            .join(Question.letter)
            .join(Letter.group)
            .where(Group.api_identifier.in_(group_api_ids))
        ).all()
    }
    for response_api_id, question_api_id in response_pairs:
        enforcer.add_named_grouping_policy(
            "g2", response_api_id, question_api_id
        )

    # p: READ on each of the subject's groups
    for group_api_id in set(group_api_ids):
        enforcer.add_policy(group_api_id, group_api_id, Action.READ.value)

    return enforcer


def enforce_stateless(
    db: Session,
    sub_api_id: str,
    obj_api_id: str,
    act: Action,
    enforcer: Enforcer | None = None,
) -> bool:
    if enforcer is None:
        enforcer = build_stateless_enforcer(db, sub_api_id)
    return enforcer.enforce(sub_api_id, obj_api_id, act.value)
