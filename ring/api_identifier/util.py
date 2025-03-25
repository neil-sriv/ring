from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Sequence, TypeVar

from fastapi import HTTPException
from sqlalchemy.exc import NoResultFound

from ring.api_identifier.api_identified_model import APIIdentified

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class APIIdentifierException(HTTPException):
    """Base exception class for API identifier related errors.

    :param model_cls: The model class that triggered the exception
    :type model_cls: type[APIIdentified]
    :param message: Optional custom error message, defaults to None
    :type message: Optional[str]
    :return: None
    :rtype: None
    """

    def __init__(
        self, model_cls: type[APIIdentified], message: Optional[str] = None
    ):
        """Initialize an APIIdentifierException.

        :param model_cls: The model class that triggered the exception
        :type model_cls: type[APIIdentified]
        :param message: Optional custom error message, defaults to None
        :type message: Optional[str]
        :return: None
        :rtype: None
        """
        super().__init__(404, detail=message)
        self.model_cls = model_cls


class IDNotFoundException(APIIdentifierException):
    """Exception raised when API identifiers cannot be found in the database.

    :param model_cls: The model class that was queried
    :type model_cls: type[APIIdentified]
    :param api_ids: List of API identifiers that were not found
    :type api_ids: list[str]
    :return: None
    :rtype: None
    """

    def __init__(self, model_cls: type[APIIdentified], api_ids: list[str]):
        """Initialize an IDNotFoundException.

        :param model_cls: The model class that was queried
        :type model_cls: type[APIIdentified]
        :param api_ids: List of API identifiers that were not found
        :type api_ids: list[str]
        :return: None
        :rtype: None
        """
        self.api_ids = api_ids
        super().__init__(
            model_cls,
            f'Could not resolve "{",".join(api_ids)}" for model class {model_cls.__name__}',
        )


API_CLS = TypeVar("API_CLS", bound=APIIdentified)


def get_model(db: Session, model_cls: type[API_CLS], api_id: str) -> API_CLS:
    """Retrieve a single model instance by its API identifier.

    :param db: SQLAlchemy database session
    :type db: Session
    :param model_cls: The model class to query
    :type model_cls: type[API_CLS]
    :param api_id: The API identifier to look up
    :type api_id: str
    :raises IDNotFoundException: If the API identifier is not found
    :return: The model instance matching the API identifier
    :rtype: API_CLS
    """
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
    """Retrieve multiple model instances by their API identifiers.

    :param db: SQLAlchemy database session
    :type db: Session
    :param model_cls: The model class to query
    :type model_cls: type[API_CLS]
    :param api_ids: List of API identifiers to look up
    :type api_ids: list[str]
    :raises IDNotFoundException: If any API identifier is not found
    :return: Sequence of model instances matching the API identifiers
    :rtype: Sequence[API_CLS]
    """
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
