from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Generic, Sequence, TypeVar
from ring.sqlalchemy_base import Base
from ring.worker.celery_app import CeleryTask

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

T = TypeVar("T", bound=Base)


@dataclass
class CollectionEvent(Generic[T]):
    model_class: type[T]
    collection_fn: Callable[..., Sequence[T]]
    operation_fn: Callable[[CeleryTask, list[int]], None]


def register_collection_event(
    model_class: type[T],
    collection_fn: Callable[..., Sequence[T]],
    operation_fn: Callable[[CeleryTask, list[int]], None],
) -> CollectionEvent[T]:
    return CollectionEvent(model_class, collection_fn, operation_fn)


def execute_collection_event(
    db: Session, event: CollectionEvent[T], task_ids: list[int]
) -> None:
    models = event.collection_fn(db, task_ids)
    event.operation_fn(models)
