from __future__ import annotations

from typing import Any, Sequence

from pydantic import BaseModel

from ring.ring_pydantic.pydantic_model import PydanticModel
from ring.sqlalchemy_base import Base


def assert_pydantic_models_json_dump_in_response_dict(
    models: Sequence[PydanticModel],
    data: dict[str, Any],
    override_pydantic_model: type[BaseModel] | None = None,
) -> None:
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
