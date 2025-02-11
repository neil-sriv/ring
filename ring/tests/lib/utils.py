from typing import Any, Sequence

from ring.ring_pydantic.pydantic_model import PydanticModel
from ring.sqlalchemy_base import Base
from ring.worker.celery_app import CeleryTask


def assert_pydantic_models_json_dump_in_response_dict(
    models: Sequence[PydanticModel], data: dict[str, Any]
) -> None:
    assert all(
        [
            model.to_pydantic().model_dump(mode="json") in data
            for model in models
        ]
    )


def assert_pydantic_model_json_dump_equivalent_to_response_dict(
    model: PydanticModel, data: dict[str, Any]
) -> None:
    assert model.to_pydantic().model_dump(mode="json") == data


def assert_api_model_not_found(
    data: dict[str, Any], model_cls: type[Base], api_ids: list[str]
) -> None:
    assert data == {
        "detail": "Model ids not found",
        "model": model_cls.__name__,
        "api_ids": api_ids,
    }


def run_celery_task(task: CeleryTask) -> None:
    # TODO(#110): Implement celery task testing
    raise NotImplementedError
