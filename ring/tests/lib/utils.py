from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Sequence
from unittest.mock import MagicMock, patch

from pydantic import BaseModel
from sqlalchemy.orm import Session

from ring.ring_pydantic.pydantic_model import PydanticModel
from ring.sqlalchemy_base import Base


def assert_pydantic_models_json_dump_in_response_dict(
    models: Sequence[PydanticModel],
    data: dict[str, Any],
    override_pydantic_model: type[BaseModel] | None = None,
) -> None:
    for model in models:
        print(model.to_pydantic().model_dump(mode="json"))
    assert all(
        [
            (
                override_pydantic_model.model_validate(model)
                if override_pydantic_model
                else model.to_pydantic()
            ).model_dump(mode="json")
            in data
            for model in models
        ]
    )


def assert_pydantic_model_json_dump_equivalent_to_response_dict(
    model: PydanticModel,
    data: dict[str, Any],
    override_pydantic_model: type[BaseModel] | None = None,
) -> None:
    pydantic_model = (
        override_pydantic_model.model_validate(model)
        if override_pydantic_model
        else model.to_pydantic()
    )
    assert pydantic_model.model_dump(mode="json") == data


def assert_pydantic_schema_json_dump_equivalent_to_response_dict(
    schema: BaseModel, data: dict[str, Any]
) -> None:
    assert schema.model_dump(mode="json") == data


def assert_api_model_not_found(
    data: dict[str, Any], model_cls: type[Base], api_ids: list[str]
) -> None:
    assert data == {
        "detail": "Model ids not found",
        "model": model_cls.__name__,
        "api_ids": api_ids,
    }


def assert_lists_equal_with_order_insensitive(
    list1: list[Any], list2: list[Any]
) -> None:
    assert sorted(list1) == sorted(list2)


def assert_sqlalchemy_object_list_equal_with_order_insensitive(
    list1: list[Base], list2: list[Base]
) -> None:
    assert sorted(list1, key=lambda x: x.id) == sorted(
        list2, key=lambda x: x.id
    )


@contextmanager
def run_scheduled_jobs_inline(db: Session) -> Iterator[MagicMock]:
    """Run ``scheduler.add_job`` callbacks against the test session.

    Production one-shot jobs use APScheduler with their own DB session.
    Unit tests share a rolled-back transaction, so jobs are invoked
    immediately with the test session instead.
    """
    from ring.async_scheduler.job_registry import JOB_REGISTRY

    def _add_job(job: Any, *args: Any, **kwargs: Any) -> None:
        job_args = list(kwargs.get("args") or [])
        name = getattr(job, "name", None)
        if name and name in JOB_REGISTRY:
            JOB_REGISTRY[name].job_function(db, *job_args)
            return
        raise AssertionError(f"Unregistered job scheduled: {job!r}")

    with patch(
        "ring.async_scheduler.scheduler.scheduler.add_job",
        side_effect=_add_job,
    ) as mock_add_job:
        yield mock_add_job


def email_draft_recipients(
    mock_send_email: MagicMock, call_index: int = 0
) -> list[str]:
    draft = mock_send_email.call_args_list[call_index].args[0]
    return list(draft.destination["ToAddresses"])


def email_draft_subject(
    mock_send_email: MagicMock, call_index: int = 0
) -> str:
    draft = mock_send_email.call_args_list[call_index].args[0]
    return draft.message["Subject"]["Data"]


def is_waiting_response_email(
    mock_send_email: MagicMock, call_index: int = 0
) -> bool:
    return (
        "waiting for your response"
        in email_draft_subject(mock_send_email, call_index).lower()
    )
