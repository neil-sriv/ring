from functools import lru_cache
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


class RingConfig(BaseSettings):
    environment: str
    sqlalchemy_database_uri: str
    JWT_SIGNING_KEY: str
    JWT_SIGNING_ALGORITHM: str


@lru_cache
def get_config() -> RingConfig:
    load_dotenv()
    return RingConfig()  # type: ignore
