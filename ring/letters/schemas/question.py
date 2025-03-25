from __future__ import annotations

from pydantic import AwareDatetime, BaseModel, ConfigDict


class QuestionBase(BaseModel):
    """Base schema for question-related operations.

    :param question_text: The text content of the question
    :type question_text: str
    """
    question_text: str


class QuestionCreate(QuestionBase):
    """Schema for creating a new question.

    :param question_text: The text content of the question
    :type question_text: str
    :param author_api_id: API identifier of the question's author, optional
    :type author_api_id: str | None
    """
    author_api_id: str | None


class Question(QuestionBase):
    """Schema representing a question in the system.

    :param question_text: The text content of the question
    :type question_text: str
    :param api_identifier: Unique API identifier for the question
    :type api_identifier: str
    :param created_at: Timestamp when the question was created
    :type created_at: AwareDatetime
    """
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str
    created_at: AwareDatetime


class QuestionUnlinked(Question):
    """Schema for question without linked relationships.

    Inherits all fields from Question but excludes relationship data.
    """
    pass
