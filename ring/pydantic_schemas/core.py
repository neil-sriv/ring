from __future__ import annotations
from pydantic import BaseModel


class ResponseMessage(BaseModel):
    message: str
