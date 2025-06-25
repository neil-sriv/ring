from __future__ import annotations

from enum import Enum

from casbin import Enforcer, Model
from sqlalchemy import select
from sqlalchemy.orm import Session

from ring.api_identifier.util import get_model
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
    """Build a stateless enforcer for a request."""
    enforcer = get_enforcer()

    # add g1 rules for user groups
    stmt = (
        select(Group.api_identifier, User.api_identifier)
        .join(Group.members)
        .where(Group.members.any(User.api_identifier == sub_api_id))
    )
    user_groups = db.execute(stmt).all()

    for group_api_id, user_api_id in user_groups:
        enforcer.add_grouping_policy(user_api_id, group_api_id)

    # add g2 rules for resource hierarchy
    stmt = (
        select(
            Group.api_identifier,
            User.api_identifier,
            Letter.api_identifier,
            Question.api_identifier,
            Response.api_identifier,
        )
        .outerjoin(Group.letters)
        .outerjoin(Group.members)
        .outerjoin(Letter.questions)
        .outerjoin(Question.responses)
        .where(
            Group.api_identifier.in_(
                [group_api_id for group_api_id, _ in user_groups]
            )
        )
    )
    resources = db.execute(stmt).all()

    for (
        group_api_id,
        user_api_id,
        letter_api_id,
        question_api_id,
        response_api_id,
    ) in resources:
        if user_api_id:
            enforcer.add_named_grouping_policy("g2", user_api_id, group_api_id)
        if letter_api_id:
            enforcer.add_named_grouping_policy(
                "g2", letter_api_id, group_api_id
            )
        if question_api_id:
            enforcer.add_named_grouping_policy(
                "g2", question_api_id, letter_api_id
            )
        if response_api_id:
            enforcer.add_named_grouping_policy(
                "g2", response_api_id, question_api_id
            )

    # add p rules for group permissions
    for group in user_groups:
        enforcer.add_policy(
            group.api_identifier, group.api_identifier, Action.READ.value
        )
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
    return enforcer.enforce(sub_api_id, obj_api_id, act)
