from __future__ import annotations

from openai.types.chat.chat_completion import ChatCompletion, CompletionUsage
from pydantic import BaseModel


class CompletionRequest(BaseModel):
    prompt: str
    max_tokens: int = 100


class CompletionResponse(BaseModel):
    completion: ChatCompletion
    text: str
    usage: CompletionUsage
