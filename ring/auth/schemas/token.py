from pydantic import BaseModel


class Token(BaseModel):
    """Authentication token schema.

    Represents the structure of an authentication token response.

    :param access_token: The JWT access token string
    :type access_token: str
    :param token_type: The type of token (e.g., "bearer")
    :type token_type: str
    """
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token payload data schema.

    Represents the data embedded within a JWT token.

    :param email: The email address of the authenticated user, defaults to None
    :type email: str | None
    """
    email: str | None = None
