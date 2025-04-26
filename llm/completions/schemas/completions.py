from __future__ import annotations

from pydantic import BaseModel


class CompletionRequest(BaseModel):
    prompt: str
    max_tokens: int = 100


class CompletionResponse(BaseModel):
    text: str
    usage: dict
