from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings


class LLMConfig(BaseSettings):
    environment: str = "development"
    root_path: str = "/api/v1"
    openai_api_key: str = "ollama"
    openai_base_url: str = "http://host.docker.internal:11434/v1"


@lru_cache
def get_config() -> LLMConfig:
    load_dotenv()
    return LLMConfig()  # type: ignore
