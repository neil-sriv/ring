from __future__ import annotations

from pydantic import BaseModel


class CompletionBase(BaseModel):
    pass


class CompletionRequest(CompletionBase):
    prompt: str


class CompletionResponse(CompletionBase):
    text: str
