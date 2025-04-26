"""Base mixin for API identifier management.

This module provides the APIIdentified mixin class that enables models to have
unique, prefixed API identifiers. It automatically generates and manages these
identifiers using UUIDs.
"""

from __future__ import annotations

from typing import Optional
from uuid import uuid4

from sqlalchemy.orm import Mapped, mapped_column


class APIIdentified:
    """Base mixin class for models that require a unique API identifier.

    Provides functionality to automatically generate and manage unique API identifiers
    for database models. Each model using this mixin must define an API_ID_PREFIX.

    Attributes:
        API_ID_PREFIX (str): Class variable that must be set by inheriting classes
        api_identifier (Mapped[str]): SQLAlchemy column storing the unique identifier string
    """

    API_ID_PREFIX: str

    api_identifier: Mapped[str] = mapped_column(unique=True, index=True)

    def __init__(self, api_prefix: Optional[str] = None) -> None:
        """Initialize an APIIdentified instance with a unique identifier.

        Args:
            api_prefix (Optional[str], optional): Custom prefix for the API identifier. Defaults to None.

        Raises:
            ValueError: If neither api_prefix nor API_ID_PREFIX is set
            AssertionError: If not used as a mixin
        """
        assert isinstance(
            self, APIIdentified
        ), "APIIdentified must be used as a mixin"
        prefix = api_prefix or getattr(self, "API_ID_PREFIX", None)
        if not prefix:
            raise ValueError("API_ID_PREFIX must be set on the class")

        self.api_identifier = f"{prefix}_{uuid4()}"
