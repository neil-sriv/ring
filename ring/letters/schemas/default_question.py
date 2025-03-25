from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DefaultQuestionBase(BaseModel):
    """Base schema for default question-related operations.

    :param question: The text content of the default question
    :type question: str
    """
    question: str


class DefaultQuestion(DefaultQuestionBase):
    """Schema representing a default question in the system.

    :param question: The text content of the default question
    :type question: str
    :param api_identifier: Unique API identifier for the default question
    :type api_identifier: str
    """
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str


class DefaultQuestionUnlinked(DefaultQuestion):
    """Schema for default question without linked relationships.

    Inherits all fields from DefaultQuestion but excludes relationship data.
    """
    pass
