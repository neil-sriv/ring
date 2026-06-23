from __future__ import annotations

from pydantic import BaseModel


class SearchUserSnippet(BaseModel):
    api_identifier: str
    name: str | None
    group_count: int


class SearchGroupSnippet(BaseModel):
    api_identifier: str
    name: str
    member_count: int
    letter_count: int


class SearchQuestionSnippet(BaseModel):
    api_identifier: str
    question_text: str
    group_name: str
    letter_api_identifier: str
    letter_number: int | None
    response_count: int


class SearchResponseSnippet(BaseModel):
    api_identifier: str
    response_text: str
    question_text: str
    letter_api_identifier: str
    letter_number: int | None
    group_name: str
    participant_name: str | None


class SearchLetterSnippet(BaseModel):
    api_identifier: str
    number: int | None
    group_name: str
    participant_count: int
    question_count: int
