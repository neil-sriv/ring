from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Sequence, TypeVar

from fastapi import HTTPException
from sqlalchemy.exc import NoResultFound

from ring.api_identifier.api_identified_model import APIIdentified

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class APIIdentifierException(HTTPException):
    def __init__(
        self, model_cls: type[APIIdentified], message: Optional[str] = None
    ):
        super().__init__(404, detail=message)
        self.model_cls = model_cls


class IDNotFoundException(APIIdentifierException):
    def __init__(self, model_cls: type[APIIdentified], api_ids: list[str]):
        self.api_ids = api_ids
        super().__init__(
            model_cls,
            f'Could not resolve "{",".join(api_ids)}" for model class {model_cls.__name__}',
        )


API_CLS = TypeVar("API_CLS", bound=APIIdentified)


def get_model(db: Session, model_cls: type[API_CLS], api_id: str) -> API_CLS:
    try:
        return (
            db.query(model_cls)
            .filter(model_cls.api_identifier == api_id)
            .one()
        )
    except NoResultFound:
        raise IDNotFoundException(model_cls, [api_id])


def get_models(
    db: Session, model_cls: type[API_CLS], api_ids: list[str]
) -> Sequence[API_CLS]:
    try:
        models = (
            db.query(model_cls)
            .filter(model_cls.api_identifier.in_(api_ids))
            .all()
        )
        if len(models) == len(api_ids):
            return models
        missing_api_ids = set(api_ids) - {
            model.api_identifier for model in models
        }
        raise IDNotFoundException(model_cls, list(missing_api_ids))
    except NoResultFound:
        raise IDNotFoundException(model_cls, api_ids)
