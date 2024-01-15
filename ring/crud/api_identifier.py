from __future__ import annotations
from sqlalchemy.exc import NoResultFound
from typing import TYPE_CHECKING, Optional, TypeVar

from ring.sqlalchemy_base import Base


if TYPE_CHECKING:
    from sqlalchemy.orm import Session

APIIdentifiedType = TypeVar("APIIdentifiedType")


class APIIdentifierException(Exception):
    def __init__(self, model_cls: type[Base], message: Optional[str] = None):
        super().__init__(message)
        self.model_cls = model_cls


class IDNotFoundException(APIIdentifierException):
    def __init__(self, model_cls: type[Base], api_id: str):
        super().__init__(
            model_cls, f'Could not resolve "{api_id}" for model class {model_cls}'
        )


def get_model(
    db: Session, model_cls: type[APIIdentifiedType], api_id: str
) -> APIIdentifiedType:
    try:
        return db.query(model_cls).filter(model_cls.api_identifier == api_id).one()
    except NoResultFound:
        raise IDNotFoundException(model_cls, api_id)
