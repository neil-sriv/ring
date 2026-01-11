"""Security utilities for Ring's authentication system.

This module provides utilities for password hashing, JWT token generation and
validation, and OAuth2 authentication. It uses bcrypt for password hashing
and JWT for token-based authentication.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from enum import Enum

from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

from ring.fastapp.config import get_config

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login/access-token")
password_hash = PasswordHash([BcryptHasher()])

ACCESS_TOKEN_TTL = 60 * 15  # 15 minutes
REFRESH_TOKEN_TTL = 60 * 60 * 24 * 30  # 30 days


class TokenType(str, Enum):
    """Enum for JWT token types."""

    ACCESS = "access"
    REFRESH = "refresh"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    Args:
        plain_password (str): The password to verify
        hashed_password (str): The hashed password to verify against

    Returns:
        bool: True if the password matches the hash, False otherwise
    """
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a secure hash of a password.

    Args:
        password (str): The password to hash

    Returns:
        str: The hashed password using bcrypt
    """
    return password_hash.hash(password)


def create_access_token(
    data: dict[str, str | datetime], expires_ttl: int = ACCESS_TOKEN_TTL
) -> str:
    """Create a JWT access token.

    Args:
        data (dict[str, str | datetime]): Data to encode in the token
        expires_ttl (int, optional): Time to live in seconds. Defaults to 15 minutes.

    Returns:
        str: The encoded JWT token

    Example:
        ```python
        token = create_access_token({"sub": user.email})
        ```
    """
    config = get_config()
    to_encode = data.copy()
    expire = datetime.now(tz=UTC) + timedelta(seconds=expires_ttl)
    to_encode.update(
        {
            "exp": expire,
            "type": TokenType.ACCESS.value,
            "jti": str(uuid.uuid4()),
        }
    )
    encoded_jwt = jwt.encode(
        to_encode,
        config.JWT_SIGNING_KEY,
        algorithm=config.JWT_SIGNING_ALGORITHM,
    )
    return encoded_jwt


def create_refresh_token(
    data: dict[str, str | datetime], expires_ttl: int = REFRESH_TOKEN_TTL
) -> str:
    """Create a JWT refresh token.

    Refresh tokens are longer-lived tokens used to obtain new access tokens
    without requiring the user to re-authenticate.

    Args:
        data (dict[str, str | datetime]): Data to encode in the token
        expires_ttl (int, optional): Time to live in seconds. Defaults to 30 days.

    Returns:
        str: The encoded JWT refresh token

    Example:
        ```python
        token = create_refresh_token({"sub": user.email})
        ```
    """
    config = get_config()
    to_encode = data.copy()
    expire = datetime.now(tz=UTC) + timedelta(seconds=expires_ttl)
    to_encode.update(
        {
            "exp": expire,
            "type": TokenType.REFRESH.value,
            "jti": str(uuid.uuid4()),
        }
    )
    encoded_jwt = jwt.encode(
        to_encode,
        config.JWT_SIGNING_KEY,
        algorithm=config.JWT_SIGNING_ALGORITHM,
    )
    return encoded_jwt


def decode_token(token: str) -> str:
    """Decode and validate a JWT token.

    Args:
        token (str): The JWT token to decode

    Returns:
        str: The email address from the token's subject claim

    Raises:
        HTTPException: If the token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            get_config().JWT_SIGNING_KEY,
            algorithms=[get_config().JWT_SIGNING_ALGORITHM],
        )
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return email


def decode_refresh_token(token: str) -> str:
    """Decode and validate a JWT refresh token.

    This function verifies that the token is a valid refresh token (not an access token)
    and returns the email from the token's subject claim.

    Args:
        token (str): The JWT refresh token to decode

    Returns:
        str: The email address from the token's subject claim

    Raises:
        HTTPException: If the token is invalid, expired, or not a refresh token
    """
    try:
        payload = jwt.decode(
            token,
            get_config().JWT_SIGNING_KEY,
            algorithms=[get_config().JWT_SIGNING_ALGORITHM],
        )
        token_type = payload.get("type")
        if token_type != TokenType.REFRESH.value:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return email
