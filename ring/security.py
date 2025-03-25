"""Security utilities for Ring's authentication system.

This module provides utilities for password hashing, JWT token generation and
validation, and OAuth2 authentication. It uses bcrypt for password hashing
and JWT for token-based authentication.
"""

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

from ring.config import get_config

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login/access-token")
password_hash = PasswordHash([BcryptHasher()])

ACCESS_TOKEN_TTL = 60 * 60 * 24 * 7  # 1 week


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
        expires_ttl (int, optional): Time to live in seconds. Defaults to 1 week.

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
    to_encode.update({"exp": expire})
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
