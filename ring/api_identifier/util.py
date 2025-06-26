"""Utility functions for API identifier management.

This module provides functions and exception classes for working with API identifiers,
including retrieving models by their API identifiers and handling related errors.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Sequence, TypeVar

from fastapi import HTTPException
from sqlalchemy.exc import NoResultFound

from ring.api_identifier.api_identified_model import APIIdentified, APIPrefix
from ring.lib.util import RegistrationDict

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class APIIdentifierException(HTTPException):
    """Base exception class for API identifier related errors.

    Attributes:
        model_cls (type[APIIdentified]): The model class that triggered the exception
        message (Optional[str]): Optional custom error message
    """

    def __init__(
        self, model_cls: type[APIIdentified], message: Optional[str] = None
    ):
        """Initialize an APIIdentifierException.

        Args:
            model_cls (type[APIIdentified]): The model class that triggered the exception
            message (Optional[str], optional): Custom error message. Defaults to None.
        """
        super().__init__(404, detail=message)
        self.model_cls = model_cls


class IDNotFoundException(APIIdentifierException):
    """Exception raised when API identifiers cannot be found in the database.

    Attributes:
        model_cls (type[APIIdentified]): The model class that was queried
        api_ids (list[str]): List of API identifiers that were not found
    """

    def __init__(self, model_cls: type[APIIdentified], api_ids: list[str]):
        """Initialize an IDNotFoundException.

        Args:
            model_cls (type[APIIdentified]): The model class that was queried
            api_ids (list[str]): List of API identifiers that were not found
        """
        self.api_ids = api_ids
        super().__init__(
            model_cls,
            f'Could not resolve "{",".join(api_ids)}" for model class {model_cls.__name__}',
        )


API_CLS = TypeVar("API_CLS", bound=APIIdentified)


@dataclass
class APIClassRegistration:
    model_class: type[APIIdentified]
    prefix: str


API_CLASS_REGISTRY: RegistrationDict[APIPrefix, APIClassRegistration] = (
    RegistrationDict("API_CLASS_REGISTRY")
)


def register_api_class(
    api_prefix: APIPrefix,
):
    def decorator(
        model_class: type[APIIdentified],
    ):
        API_CLASS_REGISTRY[api_prefix] = APIClassRegistration(
            model_class, api_prefix.value
        )
        return model_class

    return decorator


def get_class_from_prefix(prefix: str) -> type[APIIdentified]:
    return API_CLASS_REGISTRY[APIPrefix(prefix)].model_class


def get_model(db: Session, model_cls: type[API_CLS], api_id: str) -> API_CLS:
    """Retrieve a single model instance by its API identifier.

    Args:
        db (Session): SQLAlchemy database session
        model_cls (type[API_CLS]): The model class to query
        api_id (str): The API identifier to look up

    Returns:
        API_CLS: The model instance matching the API identifier

    Raises:
        IDNotFoundException: If the API identifier is not found
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

    Args:
        db (Session): SQLAlchemy database session
        model_cls (type[API_CLS]): The model class to query
        api_ids (list[str]): List of API identifiers to look up

    Returns:
        Sequence[API_CLS]: Sequence of model instances matching the API identifiers

    Raises:
        IDNotFoundException: If any API identifier is not found
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


def bulk_get_models(
    db: Session,
    api_ids: list[str],
) -> Sequence[APIIdentified]:
    """Retrieve multiple model instances by their API identifiers."""
    api_ids_by_prefix: defaultdict[APIPrefix, list[str]] = defaultdict(list)
    for api_id in api_ids:
        prefix = APIPrefix(api_id.split("_")[0])
        api_ids_by_prefix[prefix].append(api_id)
    models: list[APIIdentified] = []
    for prefix, api_ids in api_ids_by_prefix.items():
        model_cls = get_class_from_prefix(prefix)
        models.extend(get_models(db, model_cls, api_ids))
    return models
