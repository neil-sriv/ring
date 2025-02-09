from functools import lru_cache
from typing import Annotated

from dotenv import load_dotenv
from pydantic import AnyUrl, BeforeValidator
from pydantic_settings import BaseSettings


def parse_cors(origins: str) -> list[str]:
    return [origin.strip() for origin in origins.split(" ")] if origins else []


class RingConfig(BaseSettings):
    environment: str
    sqlalchemy_database_uri: str
    JWT_SIGNING_KEY: str
    JWT_SIGNING_ALGORITHM: str
    VAPID_PRIVATE_KEY: str
    root_path: str = "/api/v1"
    BUCKET_NAME: str = "rings3files"
    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str,
        BeforeValidator(parse_cors),
    ] = []


@lru_cache
def get_config() -> RingConfig:
    load_dotenv()
    return RingConfig()  # type: ignore
