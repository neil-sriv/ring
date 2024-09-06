
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class InviteBase(BaseModel):
    email: str


class InviteCreate(InviteBase):
    pass


class Invite(InviteBase):
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str
    created_at: datetime
    is_expired: bool
    token: str


class InviteUnlinked(Invite):
    pass
