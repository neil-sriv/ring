from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from typing import Literal

from google import genai
from openai import AsyncOpenAI
from pydantic import BaseModel

from llm.config import get_config

llm_config = get_config()


class LLMType(StrEnum):
    OPENAI = "openai"
    GEMINI = "gemini"


class LLMClient(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    client: AsyncOpenAI
    model: str
    mode: Literal["chat", "completions"] | None = None
    environment: Literal["development", "production"]


@lru_cache
def get_llm(llm_type: LLMType) -> LLMClient:
    if llm_type == LLMType.OPENAI:
        client = AsyncOpenAI(
            api_key=llm_config.openai_api_key,
            base_url=llm_config.ollama_base_url
            if llm_config.environment == "development"
            else llm_config.openai_base_url,
        )
        return LLMClient(
            client=client,
            model="llama3.2"
            if llm_config.environment == "development"
            else "llama3.2-70b",
            environment=llm_config.environment,
        )
    elif llm_type == LLMType.GEMINI:
        client = AsyncOpenAI(
            api_key=llm_config.gemini_api_key,
            base_url=llm_config.ollama_base_url
            if llm_config.environment == "development"
            else llm_config.gemini_base_url,
        )
        return LLMClient(
            client=client,
            model="gemma3:1b"
            if llm_config.environment == "development"
            else "models/gemini-2.0-flash",
            environment=llm_config.environment,
        )
    else:
        raise ValueError(f"Invalid LLM type: {llm_type}")
