"""Base class for SQLAlchemy models with Pydantic integration.

This module provides a base class that enables SQLAlchemy models to be easily
converted to Pydantic models for API responses.
"""
from __future__ import annotations

import json

from pydantic import BaseModel


class PydanticModel:
    """Base class for SQLAlchemy models that can be converted to Pydantic models.

    This class provides functionality to convert SQLAlchemy model instances to
    their corresponding Pydantic model representations for API responses.

    Class Attributes:
        PYDANTIC_MODEL (type[BaseModel]): The Pydantic model class to use for conversion
    """

    PYDANTIC_MODEL: type[BaseModel]

    def to_pydantic(self) -> BaseModel:
        """Convert the SQLAlchemy model instance to its Pydantic representation.

        Returns:
            BaseModel: The Pydantic model instance
        """
        return self.PYDANTIC_MODEL.model_validate(self)

    def __str__(self) -> str:
        """Convert the model to a string representation using its Pydantic model.

        Returns:
            str: String representation of the model
        """
        if self.PYDANTIC_MODEL:
            return str(self.PYDANTIC_MODEL.model_validate(self).model_dump())
        return super().__str__()

    # def __repr__(self) -> str:
    #     if self.PYDANTIC_MODEL:
    #         return str(self.PYDANTIC_MODEL.model_validate(self).model_dump())
    #     return super().__repr__()

    def __repr__(self) -> str:
        """Create a detailed string representation of the model.

        Returns:
            str: JSON string representation of the model's attributes
        """
        return json.dumps(self.__dict__, indent=4, default=str)
