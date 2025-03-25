from typing import Optional
from uuid import uuid4

from sqlalchemy.orm import Mapped, mapped_column


class APIIdentified:
    """Base mixin class for models that require a unique API identifier.

    Provides functionality to automatically generate and manage unique API identifiers
    for database models. Each model using this mixin must define an API_ID_PREFIX.

    :cvar API_ID_PREFIX: Class variable that must be set by inheriting classes
    :type API_ID_PREFIX: str
    :ivar api_identifier: SQLAlchemy column storing the unique identifier string
    :type api_identifier: Mapped[str]
    """

    API_ID_PREFIX: str

    api_identifier: Mapped[str] = mapped_column(unique=True, index=True)

    def __init__(self, api_prefix: Optional[str] = None) -> None:
        """Initialize an APIIdentified instance with a unique identifier.

        :param api_prefix: Custom prefix for the API identifier, defaults to None
        :type api_prefix: Optional[str]
        :raises ValueError: If neither api_prefix nor API_ID_PREFIX is set
        :raises AssertionError: If not used as a mixin
        :return: None
        :rtype: None
        """
        assert isinstance(
            self, APIIdentified
        ), "APIIdentified must be used as a mixin"
        prefix = api_prefix or getattr(self, "API_ID_PREFIX", None)
        if not prefix:
            raise ValueError("API_ID_PREFIX must be set on the class")

        self.api_identifier = f"{prefix}_{uuid4()}"
