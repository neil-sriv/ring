from typing import Any, Sequence

from ring.ring_pydantic.pydantic_model import PydanticModel


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
