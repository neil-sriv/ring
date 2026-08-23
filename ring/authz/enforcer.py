from __future__ import annotations

from enum import Enum
from typing import Sequence

from casbin import Enforcer, Model
from sqlalchemy import select
from sqlalchemy.orm import Session

from ring.api_identifier.api_identified_model import APIPrefix
from ring.letters.models.letter_model import Letter
from ring.letters.models.question_model import Question
from ring.letters.models.response_model import Response
from ring.notebook.models.document import Document
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


def _subject_group_api_ids(db: Session, sub_api_id: str) -> list[str]:
    return list(
        db.execute(
            select(Group.api_identifier)
            .join(Group.members)
            .where(User.api_identifier == sub_api_id)
        )
        .scalars()
        .all()
    )


def _add_subject_membership_policies(
    enforcer: Enforcer,
    db: Session,
    sub_api_id: str,
    group_api_ids: Sequence[str],
    *,
    include_all_member_g: bool,
) -> None:
    """Add g + p for the subject's groups.

    When ``include_all_member_g`` is True (full corpus build), every member of
    those groups gets a ``g`` edge — matching historical join shape. The scoped
    build only needs the subject's own ``g`` edges for enforce decisions.
    """
    if include_all_member_g:
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
    else:
        for group_api_id in group_api_ids:
            enforcer.add_grouping_policy(sub_api_id, group_api_id)

    for group_api_id in set(group_api_ids):
        enforcer.add_policy(group_api_id, group_api_id, Action.READ.value)


def _add_g2_pairs(enforcer: Enforcer, pairs: set[tuple[str, str]]) -> None:
    for child, parent in pairs:
        enforcer.add_named_grouping_policy("g2", child, parent)


def _load_full_g2(
    enforcer: Enforcer, db: Session, group_api_ids: Sequence[str]
) -> None:
    member_pairs = {
        (user_api_id, group_api_id)
        for user_api_id, group_api_id in db.execute(
            select(User.api_identifier, Group.api_identifier)
            .join(Group.members)
            .where(Group.api_identifier.in_(group_api_ids))
        ).all()
    }
    _add_g2_pairs(enforcer, member_pairs)

    letter_pairs = {
        (letter_api_id, group_api_id)
        for letter_api_id, group_api_id in db.execute(
            select(Letter.api_identifier, Group.api_identifier)
            .join(Letter.group)
            .where(Group.api_identifier.in_(group_api_ids))
        ).all()
    }
    _add_g2_pairs(enforcer, letter_pairs)

    question_pairs = {
        (question_api_id, letter_api_id)
        for question_api_id, letter_api_id in db.execute(
            select(Question.api_identifier, Letter.api_identifier)
            .join(Question.letter)
            .join(Letter.group)
            .where(Group.api_identifier.in_(group_api_ids))
        ).all()
    }
    _add_g2_pairs(enforcer, question_pairs)

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
    _add_g2_pairs(enforcer, response_pairs)

    document_pairs = {
        (document_api_id, group_api_id)
        for document_api_id, group_api_id in db.execute(
            select(Document.api_identifier, Group.api_identifier)
            .join(Document.group)
            .where(Group.api_identifier.in_(group_api_ids))
        ).all()
    }
    _add_g2_pairs(enforcer, document_pairs)


def _prefix(api_id: str) -> str:
    return api_id.split("_", 1)[0]


def _load_scoped_g2(
    enforcer: Enforcer,
    db: Session,
    group_api_ids: Sequence[str],
    resource_api_ids: Sequence[str],
) -> None:
    """Load only g2 parent chains needed for the given resource API ids."""
    response_ids = {
        api_id
        for api_id in resource_api_ids
        if _prefix(api_id) == APIPrefix.RESPONSE.value
    }
    question_ids = {
        api_id
        for api_id in resource_api_ids
        if _prefix(api_id) == APIPrefix.QUESTION.value
    }
    letter_ids = {
        api_id
        for api_id in resource_api_ids
        if _prefix(api_id) == APIPrefix.LETTER.value
    }
    user_ids = {
        api_id
        for api_id in resource_api_ids
        if _prefix(api_id) == APIPrefix.USER.value
    }
    document_ids = {
        api_id
        for api_id in resource_api_ids
        if _prefix(api_id) == APIPrefix.DOCUMENT.value
    }

    if response_ids:
        response_pairs = {
            (response_api_id, question_api_id)
            for response_api_id, question_api_id in db.execute(
                select(Response.api_identifier, Question.api_identifier)
                .join(Response.question)
                .where(Response.api_identifier.in_(response_ids))
            ).all()
        }
        _add_g2_pairs(enforcer, response_pairs)
        question_ids.update(
            question_api_id for _, question_api_id in response_pairs
        )

    if question_ids:
        question_pairs = {
            (question_api_id, letter_api_id)
            for question_api_id, letter_api_id in db.execute(
                select(Question.api_identifier, Letter.api_identifier)
                .join(Question.letter)
                .where(Question.api_identifier.in_(question_ids))
            ).all()
        }
        _add_g2_pairs(enforcer, question_pairs)
        letter_ids.update(letter_api_id for _, letter_api_id in question_pairs)

    if letter_ids:
        letter_pairs = {
            (letter_api_id, group_api_id)
            for letter_api_id, group_api_id in db.execute(
                select(Letter.api_identifier, Group.api_identifier)
                .join(Letter.group)
                .where(Letter.api_identifier.in_(letter_ids))
            ).all()
        }
        _add_g2_pairs(enforcer, letter_pairs)

    if user_ids:
        # Same membership scope as the full build: only subject's groups.
        member_pairs = {
            (user_api_id, group_api_id)
            for user_api_id, group_api_id in db.execute(
                select(User.api_identifier, Group.api_identifier)
                .join(Group.members)
                .where(User.api_identifier.in_(user_ids))
                .where(Group.api_identifier.in_(group_api_ids))
            ).all()
        }
        _add_g2_pairs(enforcer, member_pairs)

    if document_ids:
        document_pairs = {
            (document_api_id, group_api_id)
            for document_api_id, group_api_id in db.execute(
                select(Document.api_identifier, Group.api_identifier)
                .join(Document.group)
                .where(Document.api_identifier.in_(document_ids))
            ).all()
        }
        _add_g2_pairs(enforcer, document_pairs)


def build_stateless_enforcer(db: Session, sub_api_id: str) -> Enforcer:
    """Build a stateless enforcer for a request.

    Loads grouping and permission policies with separate queries (no
    letters × members × questions × responses cartesian join) and
    deduplicates before inserting into Casbin.
    """
    enforcer = get_enforcer()

    group_api_ids = _subject_group_api_ids(db, sub_api_id)
    if not group_api_ids:
        return enforcer

    _add_subject_membership_policies(
        enforcer,
        db,
        sub_api_id,
        group_api_ids,
        include_all_member_g=True,
    )
    _load_full_g2(enforcer, db, group_api_ids)
    return enforcer


def build_stateless_enforcer_for_resources(
    db: Session,
    sub_api_id: str,
    resource_api_ids: Sequence[str],
) -> Enforcer:
    """Build a Casbin enforcer with g2 limited to candidate resource chains.

    Still decides authorization via Casbin ``enforce``; only the policy corpus
    loaded for ``g2`` is scoped to ``resource_api_ids`` (plus parent links).
    """
    enforcer = get_enforcer()

    group_api_ids = _subject_group_api_ids(db, sub_api_id)
    if not group_api_ids:
        return enforcer

    _add_subject_membership_policies(
        enforcer,
        db,
        sub_api_id,
        group_api_ids,
        include_all_member_g=False,
    )
    _load_scoped_g2(enforcer, db, group_api_ids, resource_api_ids)
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
