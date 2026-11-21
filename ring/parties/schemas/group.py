from __future__ import annotations

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


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
        admin_api_identifier (str | None): Deprecated. Omit it, or send the
            caller's id. Another user's id is rejected.
    """

    # Field(deprecated=True) warns on every read.
    admin_api_identifier: str | None = Field(
        default=None,
        json_schema_extra={"deprecated": True},
    )


class GroupUpdate(BaseModel):
    """Schema for updating an existing group.

    Attributes:
        name (str | None): New name for the group, optional
        cycle_length (int | None): New cycle length in days, optional
        min_responder_ratio (float | None): Minimum share of participants who
            must respond before send (0-1). Use 0 to disable deferral. Omit or
            set null to use the default (0.5).
        min_responders (int | None): Absolute responder count that takes
            precedence over the ratio. Omit to leave unchanged. Null clears it.
    """

    name: str | None = None
    cycle_length: int | None = None
    min_responder_ratio: float | None = None
    min_responders: int | None = None


class AddMembers(BaseModel):
    """Schema for adding members to a group.

    Attributes:
        member_emails (list[str]): List of email addresses to invite
    """

    member_emails: list[str]


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
        min_responder_ratio (float | None): Configured minimum responder ratio
            (0-1), or null when using the default (0.5)
        min_responders (int | None): Absolute responder count, or null when
            the ratio gate is in effect
    """

    model_config = ConfigDict(from_attributes=True)

    api_identifier: str
    created_at: AwareDatetime
    cycle_length: int
    min_responder_ratio: float | None = None
    min_responders: int | None = None


class GroupUnlinked(Group):
    """Schema for groups without linked relationships.

    Inherits all fields from Group but excludes relationship data.
    """

    pass
