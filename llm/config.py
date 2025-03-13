from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings


class LLMConfig(BaseSettings):
    environment: str = "development"
    root_path: str = "/api/v1"


@lru_cache
def get_config() -> LLMConfig:
    load_dotenv()
    return LLMConfig()  # type: ignore 