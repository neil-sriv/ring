from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel


class RawSearchResult(BaseModel):
    raw_text: str

    class Config:
        from_attributes = True


class RawSearchResponse(BaseModel):
    results: list[RawSearchResult]
    total: int


class SearchType(str, Enum):
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    DUAL = "dual"


SearchHitType = Literal["user", "group", "letter", "question", "response"]


class SearchHit(BaseModel):
    type: SearchHitType
    api_identifier: str
    title: str
    subtitle: str | None = None
    detail: str | None = None
    href_loop_id: str | None = None
    href_group_id: str | None = None
    member_count: int | None = None
    letter_count: int | None = None
    response_count: int | None = None
    participant_count: int | None = None
    question_count: int | None = None
    group_count: int | None = None

    @classmethod
    def from_model(cls, model: Any) -> "SearchHit":
        from ring.letters.models.letter_model import Letter
        from ring.letters.models.question_model import Question
        from ring.letters.models.response_model import Response
        from ring.parties.models.group_model import Group
        from ring.parties.models.user_model import User

        if isinstance(model, User):
            return cls(
                type="user",
                api_identifier=model.api_identifier,
                title=model.name or model.email,
                subtitle=f"Member of {len(model.groups)} groups",
                group_count=len(model.groups),
            )

        if isinstance(model, Group):
            member_count = len(model.members)
            letter_count = len(model.letters)
            return cls(
                type="group",
                api_identifier=model.api_identifier,
                title=model.name,
                subtitle=f"{member_count} members • {letter_count} letters",
                href_group_id=model.api_identifier,
                member_count=member_count,
                letter_count=letter_count,
            )

        if isinstance(model, Letter):
            participant_count = len(model.participants)
            question_count = len(model.questions)
            return cls(
                type="letter",
                api_identifier=model.api_identifier,
                title=_letter_title(model.group.name, model.number),
                subtitle=(
                    f"{participant_count} participants • {question_count} questions"
                ),
                href_loop_id=model.api_identifier,
                participant_count=participant_count,
                question_count=question_count,
            )

        if isinstance(model, Question):
            letter = model.letter
            response_count = len(model.responses)
            return cls(
                type="question",
                api_identifier=model.api_identifier,
                title=_letter_title(letter.group.name, letter.number),
                subtitle=model.question_text,
                detail=f"{response_count} responses",
                href_loop_id=letter.api_identifier,
                response_count=response_count,
            )

        if isinstance(model, Response):
            question = model.question
            letter = question.letter
            author = model.participant.name or model.participant.email
            return cls(
                type="response",
                api_identifier=model.api_identifier,
                title=_letter_title(letter.group.name, letter.number),
                subtitle=model.response_text,
                detail=f"Q: {question.question_text} • by {author}",
                href_loop_id=letter.api_identifier,
            )

        raise ValueError(f"Unsupported search result model: {type(model)}")


class SearchResponse(BaseModel):
    results: list[SearchHit]
    total: int


def _letter_title(group_name: str, letter_number: int | None) -> str:
    if letter_number is None:
        return f"{group_name} - Letter"
    return f"{group_name} - Letter {letter_number}"
