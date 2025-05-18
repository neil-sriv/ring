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
def get_model_config(
    llm_type: LLMType,
    env: Literal["development", "production"],
    field: Literal["embeddings", "completions", "base_url"],
) -> str:
    return MODEL_MAPPING[llm_type][env][field]


MODEL_MAPPING = {
    LLMType.OPENAI: {
        "development": {
            "base_url": llm_config.ollama_base_url,
            "completions": "llama3.2",
            "embeddings": "nomic-embed-text",
        },
        "production": {
            "base_url": llm_config.openai_base_url,
            "completions": "llama3.2-70b",
            # "embeddings": "text-embedding-3-small",
        },
    },
    LLMType.GEMINI: {
        "development": {
            "base_url": llm_config.ollama_base_url,
            "completions": "gemma3:1b",
            "embeddings": "nomic-embed-text",
        },
        "production": {
            "base_url": llm_config.gemini_base_url,
            "completions": "models/gemini-2.0-flash",
            "embeddings": "gemini-embedding-exp-03-07",
        },
    },
}


@lru_cache
def get_llm(
    llm_type: LLMType,
    use_case: Literal["embeddings", "completions"],
) -> LLMClient:
    if llm_type == LLMType.OPENAI:
        client = AsyncOpenAI(
            api_key=llm_config.openai_api_key,
            base_url=get_model_config(
                llm_type, llm_config.environment, "base_url"
            ),
        )
        return LLMClient(
            client=client,
            model=get_model_config(llm_type, llm_config.environment, use_case),
            environment=llm_config.environment,
        )
    elif llm_type == LLMType.GEMINI:
        client = AsyncOpenAI(
            api_key=llm_config.gemini_api_key,
            base_url=get_model_config(
                llm_type, llm_config.environment, "base_url"
            ),
        )
        return LLMClient(
            client=client,
            model=get_model_config(llm_type, llm_config.environment, use_case),
            environment=llm_config.environment,
        )
    else:
        raise ValueError(f"Invalid LLM type: {llm_type}")
