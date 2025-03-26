"""Response schemas for API operations.

This module defines Pydantic models for response-related operations, including
creation, updates, and data transfer between the API and database.
"""

from __future__ import annotations

from typing import Optional

from pydantic import AwareDatetime, BaseModel, ConfigDict


class ResponseBase(BaseModel):
    """Base schema for response-related operations.

    Attributes:
        response_text (str): The text content of the response
    """

    response_text: str


class ResponseCreateBase(ResponseBase):
    """Base schema for response creation operations.

    Inherits response_text field from ResponseBase.
    """

    pass


class ResponseUpsert(ResponseCreateBase):
    """Schema for creating or updating a response.

    Attributes:
        response_text (str): The text content of the response
        participant_api_identifier (Optional[str]): API identifier of the participant, optional
        api_identifier (Optional[str]): API identifier of an existing response, optional
    """

    participant_api_identifier: Optional[str] = None
    api_identifier: Optional[str] = None


class ResponseCreate(ResponseCreateBase):
    """Schema for creating a new response.

    Attributes:
        response_text (str): The text content of the response
        question_api_identifier (str): API identifier of the question being answered
        participant_api_identifier (str): API identifier of the participant
    """

    question_api_identifier: str
    participant_api_identifier: str


class Response(ResponseBase):
    """Schema representing a response in the system.

    Attributes:
        response_text (str): The text content of the response
        api_identifier (str): Unique API identifier for the response
        created_at (AwareDatetime): Timestamp when the response was created
    """

    model_config = ConfigDict(from_attributes=True)

    api_identifier: str
    created_at: AwareDatetime


class ResponseUnlinked(Response):
    """Schema for response without linked relationships.

    Inherits all fields from Response but excludes relationship data.
    """

    pass
