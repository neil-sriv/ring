"""Utilities for handling collections of tasks and their execution.

This module provides generic utilities for collecting and executing operations
on groups of database models, particularly useful for batch processing tasks.
It uses generics to maintain type safety while providing flexibility in the
types of models and operations that can be handled.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Generic, Sequence, TypeVar

from ring.sqlalchemy_base import Base

# from ring.worker.celery_app import CeleryTask

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

T = TypeVar("T", bound=Base)


@dataclass
class CollectionEvent(Generic[T]):
    """A generic container for collection-based operations.

    This class pairs a collection function that gathers models with an operation
    function that processes them. It's generic over any SQLAlchemy model type.

    Attributes:
        model_class: The SQLAlchemy model class to operate on
        collection_fn: Function that collects models from the database
        operation_fn: Function that processes the collected models
    """

    model_class: type[T]
    collection_fn: Callable[..., Sequence[T]]
    # operation_fn: Callable[[CeleryTask, list[int]], None]


def register_collection_event(
    model_class: type[T],
    collection_fn: Callable[..., Sequence[T]],
    # operation_fn: Callable[[CeleryTask, list[int]], None],
) -> CollectionEvent[T]:
    """Register a new collection event.

    This factory function creates a CollectionEvent that pairs a collection
    function with its corresponding operation function.

    Args:
        model_class: The SQLAlchemy model class to operate on
        collection_fn: Function that collects models from the database
        operation_fn: Function that processes the collected models

    Returns:
        CollectionEvent[T]: A new collection event instance
    """
    return CollectionEvent(model_class, collection_fn, operation_fn)


def execute_collection_event(
    db: Session, event: CollectionEvent[T], task_ids: list[int]
) -> None:
    """Execute a collection event on a set of task IDs.

    This function collects models using the event's collection function and
    then processes them using its operation function.

    Args:
        db: Database session
        event: The collection event to execute
        task_ids: List of task IDs to process
    """
    models = event.collection_fn(db, task_ids)
    event.operation_fn(models)
