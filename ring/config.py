from functools import lru_cache
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


class RingConfig(BaseSettings):
    dynamo_db_host: str = f"http://{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}"
    environment: str
    sqlalchemy_database_uri: str
    JWT_SIGNING_KEY: str
    JWT_SIGNING_ALGORITHM: str


@lru_cache
def get_config() -> RingConfig:
    load_dotenv()
    return RingConfig()  # type: ignore
