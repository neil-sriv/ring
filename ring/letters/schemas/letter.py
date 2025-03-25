from __future__ import annotations

from pydantic import AwareDatetime, BaseModel, ConfigDict

from ring.letters.constants import LetterStatus


class LetterBase(BaseModel):
    """Base schema for letter-related operations.

    Base class for all letter schemas, providing common functionality.
    """
    pass


class LetterCreate(LetterBase):
    """Schema for creating a new letter.

    :param group_api_identifier: API identifier of the group to create the letter for
    :type group_api_identifier: str
    :param send_at: Scheduled time to send the letter
    :type send_at: AwareDatetime
    """
    group_api_identifier: str
    send_at: AwareDatetime


class LetterUpdate(LetterBase):
    """Schema for updating an existing letter.

    :param send_at: New scheduled time to send the letter
    :type send_at: AwareDatetime
    """
    send_at: AwareDatetime


class Letter(LetterBase):
    """Schema representing a letter in the system.

    :param api_identifier: Unique API identifier for the letter
    :type api_identifier: str
    :param number: Sequential number of the letter within its group
    :type number: int
    :param status: Current status of the letter
    :type status: LetterStatus
    :param send_at: Scheduled time to send the letter
    :type send_at: AwareDatetime
    :param created_at: Timestamp when the letter was created
    :type created_at: AwareDatetime
    """
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str
    number: int
    status: LetterStatus
    send_at: AwareDatetime
    created_at: AwareDatetime


class LetterUnlinked(Letter):
    """Schema for letter without linked relationships.

    Inherits all fields from Letter but excludes relationship data.
    """
    pass
