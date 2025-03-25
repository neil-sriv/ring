from __future__ import annotations

from typing import Optional

from pydantic import AwareDatetime, BaseModel, ConfigDict


class ResponseBase(BaseModel):
    """Base schema for response-related operations.

    :param response_text: The text content of the response
    :type response_text: str
    """
    response_text: str


class ResponseCreateBase(ResponseBase):
    """Base schema for response creation operations.

    Inherits response_text field from ResponseBase.
    """
    pass


class ResponseUpsert(ResponseCreateBase):
    """Schema for creating or updating a response.

    :param response_text: The text content of the response
    :type response_text: str
    :param participant_api_identifier: API identifier of the participant, optional
    :type participant_api_identifier: Optional[str]
    :param api_identifier: API identifier of an existing response, optional
    :type api_identifier: Optional[str]
    """
    participant_api_identifier: Optional[str] = None
    api_identifier: Optional[str] = None


class ResponseCreate(ResponseCreateBase):
    """Schema for creating a new response.

    :param response_text: The text content of the response
    :type response_text: str
    :param question_api_identifier: API identifier of the question being answered
    :type question_api_identifier: str
    :param participant_api_identifier: API identifier of the participant
    :type participant_api_identifier: str
    """
    question_api_identifier: str
    participant_api_identifier: str


class Response(ResponseBase):
    """Schema representing a response in the system.

    :param response_text: The text content of the response
    :type response_text: str
    :param api_identifier: Unique API identifier for the response
    :type api_identifier: str
    :param created_at: Timestamp when the response was created
    :type created_at: AwareDatetime
    """
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str
    created_at: AwareDatetime


class ResponseUnlinked(Response):
    """Schema for response without linked relationships.

    Inherits all fields from Response but excludes relationship data.
    """
    pass
