"""Base factory classes for test data generation.

This module provides base classes and utilities for creating test data using
the factory pattern. It includes a generic base factory for SQLAlchemy models
and a registration system for managing all factories.
"""

from __future__ import annotations

from typing import Any, Generic, Type, TypeVar, get_args

from factory.alchemy import SQLAlchemyModelFactory
from factory.base import FactoryMetaClass

from ring.lib.util import RegistrationList

T = TypeVar("T")


class BaseFactoryMeta(FactoryMetaClass):
    """Meta class for BaseFactory that automatically sets the model class.

    This meta class extracts the model type from the generic type parameter
    and sets it as the model in the factory's Meta class.

    Args:
        mcs: The meta class itself
        class_name (str): Name of the class being created
        bases (list[Type]): Base classes
        attrs (dict): Class attributes
    """

    def __new__(mcs, class_name, bases: list[Type], attrs):
        orig_bases = attrs.get("__orig_bases__", [])
        for t in orig_bases:
            if t.__name__ == "BaseFactory" and t.__module__ == __name__:
                type_args = get_args(t)
                if len(type_args) == 1:
                    if "Meta" not in attrs:
                        attrs["Meta"] = type("Meta", (), {})
                    setattr(attrs["Meta"], "model", type_args[0])
        return super().__new__(mcs, class_name, bases, attrs)


class BaseFactory(
    SQLAlchemyModelFactory, Generic[T], metaclass=BaseFactoryMeta
):
    """Base factory class for creating test data.

    This class provides the foundation for all model factories in the test suite.
    It extends SQLAlchemyModelFactory with generic type support and automatic
    model class detection.

    Attributes:
        Meta: Factory configuration (abstract = True)
    """

    class Meta:  # type: ignore
        abstract = True

    @classmethod
    def create(cls, **kwargs: Any) -> T:
        """Create and persist a new instance of the model.

        Args:
            **kwargs (Any): Override values for model attributes

        Returns:
            T: A new persisted instance of the model
        """
        return super().create(**kwargs)

    @classmethod
    def build(cls, **kwargs: Any) -> T:
        """Build a new instance of the model without persisting it.

        Args:
            **kwargs (Any): Override values for model attributes

        Returns:
            T: A new unpersisted instance of the model
        """
        return super().build(**kwargs)


ALL_FACTORIES: RegistrationList[Type[SQLAlchemyModelFactory]] = (
    RegistrationList("ALL_FACTORIES")
)


def register_factory(
    cls: Type[BaseFactory[T]],
) -> Type[BaseFactory[T]]:
    """Register a factory class for test data generation.

    This decorator function adds a factory class to the global registry
    of all factories, making it available for test data generation.

    Args:
        cls (Type[BaseFactory[T]]): The factory class to register

    Returns:
        Type[BaseFactory[T]]: The registered factory class
    """
    ALL_FACTORIES.append(cls)
    return cls
