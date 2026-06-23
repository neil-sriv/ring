from __future__ import annotations

from collections import defaultdict
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ring.api_identifier.api_identified_model import APIIdentified
from ring.letters.models.letter_model import Letter, letter_to_user_assocation
from ring.letters.models.question_model import Question
from ring.letters.models.response_model import Response
from ring.parties.models.group_model import Group
from ring.parties.models.user_group_assocation import user_group_association
from ring.parties.models.user_model import User
from ring.ring_pydantic.linked_schemas import SearchResult
from ring.search.schemas.search_snippets import (
    SearchGroupSnippet,
    SearchLetterSnippet,
    SearchQuestionSnippet,
    SearchResponseSnippet,
    SearchUserSnippet,
)


def build_search_results(
    db: Session, models: Sequence[APIIdentified]
) -> list[SearchResult]:
    """Build slim search API payloads without loading full linked graphs."""
    if not models:
        return []

    by_class: dict[type[APIIdentified], list[APIIdentified]] = defaultdict(
        list
    )
    for model in models:
        by_class[type(model)].append(model)

    snippet_by_api_id: dict[str, SearchResult] = {}

    if users := by_class.get(User):
        _add_user_snippets(db, users, snippet_by_api_id)
    if groups := by_class.get(Group):
        _add_group_snippets(db, groups, snippet_by_api_id)
    if questions := by_class.get(Question):
        _add_question_snippets(db, questions, snippet_by_api_id)
    if responses := by_class.get(Response):
        _add_response_snippets(db, responses, snippet_by_api_id)
    if letters := by_class.get(Letter):
        _add_letter_snippets(db, letters, snippet_by_api_id)

    results: list[SearchResult] = []
    for model in models:
        result = snippet_by_api_id.get(model.api_identifier)
        if result is not None:
            results.append(result)
    return results


def _add_user_snippets(
    db: Session,
    users: Sequence[User],
    snippet_by_api_id: dict[str, SearchResult],
) -> None:
    user_ids = [user.id for user in users]
    group_counts = dict(
        db.execute(
            select(
                user_group_association.c.user_id,
                func.count(),
            )
            .where(user_group_association.c.user_id.in_(user_ids))
            .group_by(user_group_association.c.user_id)
        ).all()
    )
    for user in users:
        snippet_by_api_id[user.api_identifier] = SearchResult(
            model=SearchUserSnippet(
                api_identifier=user.api_identifier,
                name=user.name,
                group_count=group_counts.get(user.id, 0),
            ),
            type=SearchUserSnippet.__name__,
        )


def _add_group_snippets(
    db: Session,
    groups: Sequence[Group],
    snippet_by_api_id: dict[str, SearchResult],
) -> None:
    group_ids = [group.id for group in groups]
    member_counts = dict(
        db.execute(
            select(
                user_group_association.c.group_id,
                func.count(),
            )
            .where(user_group_association.c.group_id.in_(group_ids))
            .group_by(user_group_association.c.group_id)
        ).all()
    )
    letter_counts = dict(
        db.execute(
            select(Letter.group_id, func.count())
            .where(Letter.group_id.in_(group_ids))
            .group_by(Letter.group_id)
        ).all()
    )
    for group in groups:
        snippet_by_api_id[group.api_identifier] = SearchResult(
            model=SearchGroupSnippet(
                api_identifier=group.api_identifier,
                name=group.name,
                member_count=member_counts.get(group.id, 0),
                letter_count=letter_counts.get(group.id, 0),
            ),
            type=SearchGroupSnippet.__name__,
        )


def _add_question_snippets(
    db: Session,
    questions: Sequence[Question],
    snippet_by_api_id: dict[str, SearchResult],
) -> None:
    question_api_ids = [question.api_identifier for question in questions]
    rows = db.execute(
        select(
            Question.api_identifier,
            Question.question_text,
            Letter.api_identifier,
            Letter.number,
            Group.name,
            func.count(Response.id),
        )
        .join(Letter, Question.letter_id == Letter.id)
        .join(Group, Letter.group_id == Group.id)
        .outerjoin(Response, Response.question_id == Question.id)
        .where(Question.api_identifier.in_(question_api_ids))
        .group_by(
            Question.id,
            Question.api_identifier,
            Question.question_text,
            Letter.api_identifier,
            Letter.number,
            Group.name,
        )
    ).all()
    for (
        api_identifier,
        question_text,
        letter_api_identifier,
        letter_number,
        group_name,
        response_count,
    ) in rows:
        snippet_by_api_id[api_identifier] = SearchResult(
            model=SearchQuestionSnippet(
                api_identifier=api_identifier,
                question_text=question_text,
                group_name=group_name,
                letter_api_identifier=letter_api_identifier,
                letter_number=letter_number,
                response_count=response_count,
            ),
            type=SearchQuestionSnippet.__name__,
        )


def _add_response_snippets(
    db: Session,
    responses: Sequence[Response],
    snippet_by_api_id: dict[str, SearchResult],
) -> None:
    response_api_ids = [response.api_identifier for response in responses]
    rows = db.execute(
        select(
            Response.api_identifier,
            Response.response_text,
            Question.question_text,
            Letter.api_identifier,
            Letter.number,
            Group.name,
            User.name,
        )
        .join(Question, Response.question_id == Question.id)
        .join(Letter, Question.letter_id == Letter.id)
        .join(Group, Letter.group_id == Group.id)
        .join(User, Response.participant_id == User.id)
        .where(Response.api_identifier.in_(response_api_ids))
    ).all()
    for (
        api_identifier,
        response_text,
        question_text,
        letter_api_identifier,
        letter_number,
        group_name,
        participant_name,
    ) in rows:
        snippet_by_api_id[api_identifier] = SearchResult(
            model=SearchResponseSnippet(
                api_identifier=api_identifier,
                response_text=response_text,
                question_text=question_text,
                letter_api_identifier=letter_api_identifier,
                letter_number=letter_number,
                group_name=group_name,
                participant_name=participant_name,
            ),
            type=SearchResponseSnippet.__name__,
        )


def _add_letter_snippets(
    db: Session,
    letters: Sequence[Letter],
    snippet_by_api_id: dict[str, SearchResult],
) -> None:
    letter_ids = [letter.id for letter in letters]
    participant_counts = dict(
        db.execute(
            select(
                letter_to_user_assocation.c.letter_id,
                func.count(),
            )
            .where(letter_to_user_assocation.c.letter_id.in_(letter_ids))
            .group_by(letter_to_user_assocation.c.letter_id)
        ).all()
    )
    question_counts = dict(
        db.execute(
            select(Question.letter_id, func.count())
            .where(Question.letter_id.in_(letter_ids))
            .group_by(Question.letter_id)
        ).all()
    )
    rows = db.execute(
        select(Letter.id, Letter.api_identifier, Letter.number, Group.name)
        .join(Group, Letter.group_id == Group.id)
        .where(Letter.id.in_(letter_ids))
    ).all()
    for letter_id, api_identifier, number, group_name in rows:
        snippet_by_api_id[api_identifier] = SearchResult(
            model=SearchLetterSnippet(
                api_identifier=api_identifier,
                number=number,
                group_name=group_name,
                participant_count=participant_counts.get(letter_id, 0),
                question_count=question_counts.get(letter_id, 0),
            ),
            type=SearchLetterSnippet.__name__,
        )
