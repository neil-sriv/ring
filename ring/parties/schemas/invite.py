from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, ConfigDict

from ring.parties.schemas.one_time_token import WithTokenMixin


class InviteBase(BaseModel):
    email: str


class InviteCreate(InviteBase):
    group_api_id: str


class Invite(InviteBase, WithTokenMixin):
    model_config = ConfigDict(from_attributes=True)

    api_identifier: str
    created_at: datetime


class InviteUnlinked(Invite):
    pass
