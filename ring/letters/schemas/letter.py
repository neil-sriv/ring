"""Letter schemas for API operations.

This module defines Pydantic models for letter-related operations, including
creation, updates, and data transfer between the API and database.
"""

from __future__ import annotations

from pydantic import AwareDatetime, BaseModel, ConfigDict

from ring.letters.constants import LetterStatus, LetterType


class LetterBase(BaseModel):
    """Base schema for letter-related operations.

    Base class for all letter schemas, providing common functionality.
    """

    pass


class LetterCreate(LetterBase):
    """Schema for creating a new letter.

    Attributes:
        group_api_identifier (str): API identifier of the group to create the letter for
        send_at (AwareDatetime): Scheduled time to send the letter
        responder_api_identifiers (list[str] | None): If set, only these group members
            may respond; if omitted or empty, use group default (everyone).
    """

    group_api_identifier: str
    send_at: AwareDatetime
    title: str | None = None
    responder_api_identifiers: list[str] | None = None


class ReplaceLetterResponderAllowlist(BaseModel):
    """Replace who may respond on this letter (adhoc override or cyclic).

    Empty list clears the letter override and uses the group default.
    """

    user_api_identifiers: list[str]


class LetterUpdate(LetterBase):
    """Schema for updating an existing letter.

    Attributes:
        send_at (AwareDatetime): New scheduled time to send the letter
    """

    send_at: AwareDatetime | None = None
    title: str | None = None
    status: LetterStatus | None = None


class Letter(LetterBase):
    """Schema representing a letter in the system.

    Attributes:
        api_identifier (str): Unique API identifier for the letter
        number (int): Sequential number of the letter within its group
        status (LetterStatus): Current status of the letter
        send_at (AwareDatetime): Scheduled time to send the letter
        created_at (AwareDatetime): Timestamp when the letter was created
    """

    model_config = ConfigDict(from_attributes=True)

    api_identifier: str
    number: int | None = None
    status: LetterStatus
    send_at: AwareDatetime
    created_at: AwareDatetime
    title: str | None = None
    letter_type: LetterType


class LetterUnlinked(Letter):
    """Schema for letter without linked relationships.

    Inherits all fields from Letter but excludes relationship data.
    """

    pass
