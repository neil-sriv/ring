from sqlalchemy.orm import Session
from secrets import token_urlsafe
from ring.parties.models.one_time_token_model import OneTimeToken


class TokenExpiredError(Exception):
    pass


class TokenAlreadyUsedError(Exception):
    pass


def _use_token(token: OneTimeToken) -> OneTimeToken:
    token.used = True
    return token


def validate_token(db: Session, token: OneTimeToken) -> OneTimeToken:
    if token.is_expired:
        raise TokenExpiredError
    if token.used:
        raise TokenAlreadyUsedError
    return token


def generate_token(token: str | None = None) -> OneTimeToken:
    if not token:
        token = token_urlsafe(32)
    return OneTimeToken.create(token)


def validate_and_use_token(db: Session, token: OneTimeToken) -> OneTimeToken:
    validate_token(db, token)
    _use_token(token)
    return token
