"""CRUD operations for one-time tokens."""

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

    :param db: Database session
    :type db: Session
    :param token: Token string to look up
    :type token: str
    :return: Found token or None
    :rtype: OneTimeToken | None
    """
    return db.scalar(
        select(OneTimeToken).filter(
            OneTimeToken.token == token,
        )
    )


def _use_token(token: OneTimeToken) -> OneTimeToken:
    """Mark a token as used.

    :param token: Token to mark as used
    :type token: OneTimeToken
    :return: Updated token
    :rtype: OneTimeToken
    """
    token.used = True
    return token


def validate_token(db: Session, token: OneTimeToken) -> OneTimeToken:
    """Validate that a token can be used.

    :param db: Database session
    :type db: Session
    :param token: Token to validate
    :type token: OneTimeToken
    :return: Valid token
    :rtype: OneTimeToken
    :raises TokenExpiredError: If the token has expired
    :raises TokenAlreadyUsedError: If the token has already been used
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

    :param type: Type of token to generate
    :type type: TokenType
    :param email: Associated email address
    :type email: str
    :param token: Optional predefined token string, defaults to None
    :type token: str | None, optional
    :return: Generated token
    :rtype: OneTimeToken
    """
    if not token:
        token = token_urlsafe(32)
    return OneTimeToken.create(token, type, email=email)


def validate_and_use_token(db: Session, token: OneTimeToken) -> OneTimeToken:
    """Validate a token and mark it as used.

    :param db: Database session
    :type db: Session
    :param token: Token to validate and use
    :type token: OneTimeToken
    :return: Used token
    :rtype: OneTimeToken
    :raises TokenExpiredError: If the token has expired
    :raises TokenAlreadyUsedError: If the token has already been used
    """
    validate_token(db, token)
    _use_token(token)
    return token
