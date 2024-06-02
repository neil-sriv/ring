from functools import lru_cache
from typing import Annotated
from pydantic import AnyUrl, BeforeValidator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


def parse_cors(origins: str) -> list[str]:
    return [origin.strip() for origin in origins.split(",")] if origins else []


class RingConfig(BaseSettings):
    environment: str
    sqlalchemy_database_uri: str
    JWT_SIGNING_KEY: str
    JWT_SIGNING_ALGORITHM: str
    root_path: str = "/api/v1"
    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors)
    ] = []


@lru_cache
def get_config() -> RingConfig:
    load_dotenv()
    return RingConfig()  # type: ignore
