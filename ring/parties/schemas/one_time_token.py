from __future__ import annotations

from typing import Any

from pydantic import Field, computed_field


class WithTokenMixin:
    """Mixin class for schemas that include a one-time token.

    This mixin provides access to token-related fields while excluding the
    underlying token object from serialization.

    Attributes:
        one_time_token (Any): Reference to the token object (excluded from serialization)
        token (str): The token string (computed property)
        is_expired (bool): Whether the token has expired (computed property)
    """

    one_time_token: Any = Field(exclude=True)

    @computed_field
    @property
    def token(self) -> str:
        """Get the token string.

        :return: Token string
        :rtype: str
        """
        return self.one_time_token.token

    @computed_field
    @property
    def is_expired(self) -> bool:
        """Check if the token has expired.

        :return: True if expired, False otherwise
        :rtype: bool
        """
        return self.one_time_token.is_expired
