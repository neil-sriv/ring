from typing import Generic, Mapping, TypeVar

_KT = TypeVar("_KT")
_VT = TypeVar("_VT")


class RegistrationDict(Mapping[_KT, _VT], Generic[_KT, _VT]):
    def __init__(self, name: str) -> None:
        self.name = name
        self.dict: dict = {}  # type: ignore


T = TypeVar("T")


def get_all_subclasses(class_: type[T]) -> list[type[T]]:
    classes = [class_]
    for subclass in class_.__subclasses__():
        classes.extend(get_all_subclasses(subclass))
    return classes
