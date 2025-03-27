"""Question schemas for API operations.

This module defines Pydantic models for question-related operations, including
creation and data transfer between the API and database.
"""

from __future__ import annotations

from pydantic import AwareDatetime, BaseModel, ConfigDict


class QuestionBase(BaseModel):
    """Base schema for question-related operations.

    Attributes:
        question_text (str): The text content of the question
    """

    question_text: str


class QuestionCreate(QuestionBase):
    """Schema for creating a new question.

    Attributes:
        question_text (str): The text content of the question
        author_api_id (str | None): API identifier of the question's author, optional
    """

    author_api_id: str | None


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


class QuestionUnlinked(Question):
    """Schema for question without linked relationships.

    Inherits all fields from Question but excludes relationship data.
    """

    pass
