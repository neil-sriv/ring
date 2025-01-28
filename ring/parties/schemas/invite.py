from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from ring.parties.schemas.one_time_token import WithTokenMixin


class InviteBase(BaseModel):
    email: str

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, email: str) -> str:
        return email.lower()


class InviteCreate(InviteBase):
    group_api_id: str


class Invite(InviteBase, WithTokenMixin):
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str
    created_at: datetime


class InviteUnlinked(Invite):
    pass
