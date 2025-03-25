"""Utility classes and functions for registration and type management.

This module provides generic container classes for registration patterns and
utility functions for working with Python types and class hierarchies.
"""

from collections.abc import Mapping, Sequence
from typing import Generic, TypeVar, overload

_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


class RegistrationDict(Mapping[_KT, _VT], Generic[_KT, _VT]):
    """A dictionary-like container for registering named key-value pairs.

    This class implements the Mapping protocol and can be used to maintain
    a registry of items with type safety through generics.

    Args:
        name (str): Identifier for this registration dictionary
    """

    def __init__(self, name: str) -> None:
        """Initialize a new registration dictionary.

        Args:
            name (str): Identifier for this registration dictionary
        """
        self.name = name
        self.dict: dict = {}  # type: ignore


class RegistrationList(Sequence[_KT], Generic[_KT]):
    """A list-like container for registering items in sequence.

    This class implements the Sequence protocol and provides type-safe
    registration of items through generics.

    Args:
        name (str): Identifier for this registration list
    """

    def __init__(self, name: str) -> None:
        """Initialize a new registration list.

        Args:
            name (str): Identifier for this registration list
        """
        self.name = name
        self.list: list[_KT] = []  # type: ignore

    def append(self, item: _KT) -> None:
        """Add an item to the end of the list.

        Args:
            item (_KT): Item to append
        """
        self.list.append(item)

    @overload
    def __getitem__(self, index: int) -> _KT: ...

    @overload
    def __getitem__(self, index: slice) -> list[_KT]: ...

    def __getitem__(self, index: int | slice):  # type: ignore
        """Get an item or slice of items from the list.

        Args:
            index (int | slice): Integer index or slice object

        Returns:
            _KT | list[_KT]: Single item or list of items

        Raises:
            IndexError: If index is out of range
        """
        return self.list[index]

    def __len__(self) -> int:
        """Get the number of items in the list.

        Returns:
            int: Length of the list
        """
        return len(self.list)


T = TypeVar("T")


def get_all_subclasses(class_: type[T]) -> list[type[T]]:
    """Recursively get all subclasses of a class.

    Args:
        class_ (type[T]): Class to get subclasses for

    Returns:
        list[type[T]]: List of all subclasses including nested subclasses
    """
    classes = [class_]
    for subclass in class_.__subclasses__():
        classes.extend(get_all_subclasses(subclass))
    return classes
