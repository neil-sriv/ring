from secrets import token_urlsafe

from sqlalchemy import select
from sqlalchemy.orm import Session

from ring.parties.models.one_time_token_model import OneTimeToken, TokenType


class TokenExpiredError(Exception):
    pass


class TokenAlreadyUsedError(Exception):
    pass


def get_ott_by_token(db: Session, token: str) -> OneTimeToken | None:
    return db.scalar(
        select(OneTimeToken).filter(
            OneTimeToken.token == token,
        )
    )


def _use_token(token: OneTimeToken) -> OneTimeToken:
    token.used = True
    return token


def validate_token(db: Session, token: OneTimeToken) -> OneTimeToken:
    if token.is_expired:
        raise TokenExpiredError
    if token.used:
        raise TokenAlreadyUsedError
    return token


def generate_token(
    type: TokenType, email: str, token: str | None = None
) -> OneTimeToken:
    if not token:
        token = token_urlsafe(32)
    return OneTimeToken.create(token, type, email=email)


def validate_and_use_token(db: Session, token: OneTimeToken) -> OneTimeToken:
    validate_token(db, token)
    _use_token(token)
    return token
