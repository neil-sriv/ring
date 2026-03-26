from __future__ import annotations

from pydantic import AwareDatetime, BaseModel, ConfigDict


class GroupBase(BaseModel):
    """Base schema for group-related operations.

    Attributes:
        name (str): Name of the group
    """

    name: str


class GroupCreate(GroupBase):
    """Schema for creating a new group.

    Attributes:
        name (str): Name of the group (inherited from GroupBase)
        admin_api_identifier (str): API identifier of the user who will be admin
    """

    admin_api_identifier: str


class GroupUpdate(BaseModel):
    """Schema for updating an existing group.

    Attributes:
        name (str | None): New name for the group, optional
        cycle_length (int | None): New cycle length in days, optional
    """

    name: str | None = None
    cycle_length: int | None = None


class AddMembers(BaseModel):
    """Schema for adding members to a group.

    Attributes:
        member_emails (list[str]): List of email addresses to invite
    """

    member_emails: list[str]


class ReplaceResponderAllowlist(BaseModel):
    """Replace who may respond to cyclic loops in this group.

    Empty list means everyone in the group may respond (default).
    """

    user_api_identifiers: list[str]


class ReplaceDefaultQuestions(BaseModel):
    """Schema for replacing a group's default questions.

    Attributes:
        questions (list[str]): New list of default questions
    """

    questions: list[str]


class Group(GroupBase):
    """Schema representing a group in the system.

    Attributes:
        name (str): Name of the group (inherited from GroupBase)
        api_identifier (str): Unique API identifier for the group
        created_at (AwareDatetime): Timestamp of group creation
        cycle_length (int): Number of days between letters
    """

    model_config = ConfigDict(from_attributes=True)

    api_identifier: str
    created_at: AwareDatetime
    cycle_length: int


class GroupUnlinked(Group):
    """Schema for groups without linked relationships.

    Inherits all fields from Group but excludes relationship data.
    """

    pass
