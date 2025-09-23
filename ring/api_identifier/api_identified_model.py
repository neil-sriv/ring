"""Base mixin for API identifier management.

This module provides the APIIdentified mixin class that enables models to have
unique, prefixed API identifiers. It automatically generates and manages these
identifiers using UUIDs.
"""

from __future__ import annotations

from enum import Enum
from uuid import uuid4

from sqlalchemy.orm import Mapped, mapped_column


class APIPrefix(str, Enum):
    USER = "usr"
    GROUP = "grp"
    INVITE = "inv"
    LETTER = "lttr"
    QUESTION = "qstn"
    RESPONSE = "rspn"
    DEFAULT_QUESTION = "dfqstn"
    SUBSCRIPTION = "sbscrp"
    DOCUMENT = "dcmnt"


class APIIdentified:
    """Base mixin class for models that require a unique API identifier.

    Provides functionality to automatically generate and manage unique API identifiers
    for database models. Each model using this mixin must define an API_ID_PREFIX.

    Attributes:
        API_ID_PREFIX (Union[str, Enum]): Class variable that must be set by inheriting classes
        api_identifier (Mapped[str]): SQLAlchemy column storing the unique identifier string
    """

    API_ID_PREFIX: APIPrefix

    api_identifier: Mapped[str] = mapped_column(unique=True, index=True)

    def __init__(self) -> None:
        """Initialize an APIIdentified instance with a unique identifier.

        Args:
            None

        Raises:
            AssertionError: If not used as a mixin
        """
        assert isinstance(
            self, APIIdentified
        ), "APIIdentified must be used as a mixin"
        assert hasattr(
            self, "API_ID_PREFIX"
        ), "API_ID_PREFIX must be set on the class"
        prefix = self.API_ID_PREFIX

        self.api_identifier = f"{prefix.value}_{uuid4()}"
