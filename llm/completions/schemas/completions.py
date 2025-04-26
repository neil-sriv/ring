from __future__ import annotations

import json
from typing import Optional

from jambo.schema_converter import SchemaConverter
from openai.types.chat.chat_completion import ChatCompletion, CompletionUsage
from pydantic import BaseModel, computed_field


class CompletionRequest(BaseModel):
    prompt: str
    max_tokens: int = 100
    output_schema_definition: str

    # @computed_field
    # @property
    # def output_schema(self) -> BaseModel | None:
    #     if self.output_schema_definition is None:
    #         return None
    #     d = json.loads(self.output_schema_definition)
    #     return SchemaConverter.build(d)


class CompletionResponse(BaseModel):
    # completion: ChatCompletion
    text: str
    # usage: CompletionUsage
    output_schema: str


class Refusal(BaseModel):
    message: str


class Default(BaseModel):
    message: str
