"""Authentication token schemas.

This module defines Pydantic models for authentication tokens and their payload data,
including the structure of JWT tokens and the data they contain.
"""

from pydantic import BaseModel


class Token(BaseModel):
    """Authentication token schema.

    Represents the structure of an authentication token response.

    Attributes:
        access_token (str): The JWT access token string
        token_type (str): The type of token (e.g., "bearer")
    """
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token payload data schema.

    Represents the data embedded within a JWT token.

    Attributes:
        email (str | None): The email address of the authenticated user. Defaults to None.
    """
    email: str | None = None
