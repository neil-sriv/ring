from __future__ import annotations

from pydantic import AwareDatetime, BaseModel, ConfigDict, field_validator

from ring.parties.schemas.one_time_token import WithTokenMixin


class InviteBase(BaseModel):
    """Base schema for invite-related operations.

    Attributes:
        email (str): Email address of the invitee (automatically converted to lowercase)
    """

    email: str

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, email: str) -> str:
        """Validate and normalize email address.

        :param email: Raw email address
        :type email: str
        :return: Lowercase email address
        :rtype: str
        """
        return email.lower()


class InviteCreate(InviteBase):
    """Schema for creating a new invite.

    Attributes:
        email (str): Email address of the invitee (inherited from InviteBase)
        group_api_id (str): API identifier of the group to invite to
    """

    group_api_id: str


class Invite(InviteBase, WithTokenMixin):
    """Schema representing an invite in the system.

    Attributes:
        email (str): Email address of the invitee (inherited from InviteBase)
        token (str): One-time token string (inherited from WithTokenMixin)
        api_identifier (str): Unique API identifier for the invite
        created_at (AwareDatetime): Timestamp of invite creation
    """

    model_config = ConfigDict(from_attributes=True)

    api_identifier: str
    created_at: AwareDatetime


class InviteUnlinked(Invite):
    """Schema for invites without linked relationships.

    Inherits all fields from Invite but excludes relationship data.
    """

    pass
