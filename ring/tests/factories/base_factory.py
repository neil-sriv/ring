from __future__ import annotations

from typing import Any, Generic, Type, TypeVar, get_args

from factory.alchemy import SQLAlchemyModelFactory
from factory.base import FactoryMetaClass

T = TypeVar("T")


class BaseFactoryMeta(FactoryMetaClass):
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
    class Meta:
        abstract = True

    @classmethod
    def create(cls, **kwargs: Any) -> T:
        return super().create(**kwargs)

    @classmethod
    def build(cls, **kwargs: Any) -> T:
        return super().build(**kwargs)
