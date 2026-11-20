"""Question schemas for API operations.

This module defines Pydantic models for question-related operations, including
creation and data transfer between the API and database.
"""

from __future__ import annotations

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class QuestionBase(BaseModel):
    """Base schema for question-related operations.

    Attributes:
        question_text (str): The text content of the question
    """

    question_text: str


class QuestionCreate(QuestionBase):
    """Schema for creating a new question.

    The author is always the signed-in caller. ``author_api_id`` remains
    only so older clients can keep sending it.

    Attributes:
        question_text (str): The text content of the question
        author_api_id (str | None): Deprecated. Omit it, send null, or send
            the caller's id. Another user's id is rejected.
    """

    # OpenAPI deprecation only. Field(deprecated=True) warns on every read,
    # including when the client omits the field.
    author_api_id: str | None = Field(
        default=None,
        json_schema_extra={"deprecated": True},
    )


class QuestionReorder(BaseModel):
    question_api_identifiers: list[str]


class Question(QuestionBase):
    """Schema representing a question in the system.

    Attributes:
        question_text (str): The text content of the question
        api_identifier (str): Unique API identifier for the question
        created_at (AwareDatetime): Timestamp when the question was created
    """

    model_config = ConfigDict(from_attributes=True)

    api_identifier: str
    created_at: AwareDatetime
    position: int | None = None


class QuestionUnlinked(Question):
    """Schema for question without linked relationships.

    Inherits all fields from Question but excludes relationship data.
    """

    pass


class GenerateQuestionRequest(BaseModel):
    prompt: str


class GenerateQuestionResponse(BaseModel):
    generated_text: str
