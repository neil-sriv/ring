from typing import Generic, TypeVar, overload

from collections.abc import Mapping, Sequence

_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


class RegistrationDict(Mapping[_KT, _VT], Generic[_KT, _VT]):
    def __init__(self, name: str) -> None:
        self.name = name
        self.dict: dict = {}  # type: ignore


class RegistrationList(Sequence[_KT], Generic[_KT]):
    def __init__(self, name: str) -> None:
        self.name = name
        self.list: list[_KT] = []  # type: ignore

    def append(self, item: _KT) -> None:
        self.list.append(item)

    @overload
    def __getitem__(self, index: int) -> _KT: ...

    @overload
    def __getitem__(self, index: slice) -> list[_KT]: ...

    def __getitem__(self, index: int | slice):  # type: ignore
        return self.list[index]

    def __len__(self) -> int:
        return len(self.list)


T = TypeVar("T")


def get_all_subclasses(class_: type[T]) -> list[type[T]]:
    classes = [class_]
    for subclass in class_.__subclasses__():
        classes.extend(get_all_subclasses(subclass))
    return classes
