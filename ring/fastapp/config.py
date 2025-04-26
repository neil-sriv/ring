"""Configuration management for Ring.

This module provides configuration settings for the Ring application using Pydantic's
BaseSettings. It loads configuration from environment variables and provides type-safe
access to settings like database URIs, JWT keys, and CORS origins.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from dotenv import load_dotenv
from pydantic import AnyUrl, BeforeValidator
from pydantic_settings import BaseSettings


def parse_cors(origins: str) -> list[str]:
    """Parse CORS origins from a space-separated string.

    Args:
        origins (str): Space-separated string of allowed origins

    Returns:
        list[str]: List of cleaned origin URLs
    """
    return [origin.strip() for origin in origins.split(" ")] if origins else []


class RingConfig(BaseSettings):
    """Configuration settings for Ring.

    This class defines all configuration settings for the Ring application,
    using Pydantic for validation and type safety. Settings are loaded from
    environment variables.

    Attributes:
        environment (str): Current environment (e.g., "development", "production")
        sqlalchemy_database_uri (str): Database connection string
        JWT_SIGNING_KEY (str): Key used for signing JWTs
        JWT_SIGNING_ALGORITHM (str): Algorithm used for JWT signing
        VAPID_PRIVATE_KEY (str): Private key for VAPID web push notifications
        root_path (str): Base path for API routes (default: "/api/v1")
        BUCKET_NAME (str): S3 bucket name for file storage (default: "rings3files")
        BACKEND_CORS_ORIGINS (list[AnyUrl] | str): List of allowed CORS origins
    """

    environment: str
    sqlalchemy_database_uri: str
    cockroach_database_uri: str
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
    """Get the Ring configuration, with caching.

    This function loads environment variables and returns a cached RingConfig
    instance. The @lru_cache decorator ensures we only load the configuration
    once per process.

    Returns:
        RingConfig: The application configuration
    """
    load_dotenv()
    return RingConfig()  # type: ignore
