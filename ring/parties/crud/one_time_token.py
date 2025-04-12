"""CRUD operations for one-time tokens.

This module provides functions for managing one-time tokens used in features
like group invitations and password resets, including validation and expiration.
"""
from __future__ import annotations

from secrets import token_urlsafe

from sqlalchemy import select
from sqlalchemy.orm import Session

from ring.parties.models.one_time_token_model import OneTimeToken, TokenType


class TokenExpiredError(Exception):
    """Exception raised when attempting to use an expired token."""

    pass


class TokenAlreadyUsedError(Exception):
    """Exception raised when attempting to use a token that has already been used."""

    pass


def get_ott_by_token(db: Session, token: str) -> OneTimeToken | None:
    """Get a one-time token by its token string.

    Args:
        db (Session): Database session
        token (str): Token string to look up

    Returns:
        OneTimeToken | None: Found token or None
    """
    return db.scalar(
        select(OneTimeToken).filter(
            OneTimeToken.token == token,
        )
    )


def _use_token(token: OneTimeToken) -> OneTimeToken:
    """Mark a token as used.

    Args:
        token (OneTimeToken): Token to mark as used

    Returns:
        OneTimeToken: Updated token
    """
    token.used = True
    return token


def validate_token(db: Session, token: OneTimeToken) -> OneTimeToken:
    """Validate that a token can be used.

    Args:
        db (Session): Database session
        token (OneTimeToken): Token to validate

    Returns:
        OneTimeToken: Valid token

    Raises:
        TokenExpiredError: If the token has expired
        TokenAlreadyUsedError: If the token has already been used
    """
    if token.is_expired:
        raise TokenExpiredError
    if token.used:
        raise TokenAlreadyUsedError
    return token


def generate_token(
    type: TokenType, email: str, token: str | None = None
) -> OneTimeToken:
    """Generate a new one-time token.

    Args:
        type (TokenType): Type of token to generate
        email (str): Associated email address
        token (str | None, optional): Optional predefined token string. Defaults to None.

    Returns:
        OneTimeToken: Generated token
    """
    if not token:
        token = token_urlsafe(32)
    return OneTimeToken.create(token, type, email=email)


def validate_and_use_token(db: Session, token: OneTimeToken) -> OneTimeToken:
    """Validate a token and mark it as used.

    Args:
        db (Session): Database session
        token (OneTimeToken): Token to validate and use

    Returns:
        OneTimeToken: Used token

    Raises:
        TokenExpiredError: If the token has expired
        TokenAlreadyUsedError: If the token has already been used
    """
    validate_token(db, token)
    _use_token(token)
    return token
