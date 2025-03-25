"""Default question schemas for API operations.

This module defines Pydantic models for default question-related operations,
including data transfer between the API and database.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DefaultQuestionBase(BaseModel):
    """Base schema for default question-related operations.

    Attributes:
        question (str): The text content of the default question
    """
    question: str


class DefaultQuestion(DefaultQuestionBase):
    """Schema representing a default question in the system.

    Attributes:
        question (str): The text content of the default question
        api_identifier (str): Unique API identifier for the default question
    """
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str


class DefaultQuestionUnlinked(DefaultQuestion):
    """Schema for default question without linked relationships.

    Inherits all fields from DefaultQuestion but excludes relationship data.
    """
    pass
