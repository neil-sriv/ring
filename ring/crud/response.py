from __future__ import annotations
from typing import TYPE_CHECKING, Sequence

from ring.crud import api_identifier as api_identifier_crud
from ring.postgres_models.letter_model import Letter
from ring.postgres_models.response_model import Response
from ring.pydantic_schemas.response import Response as ResponseUpdate

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_response(db: Session, response_api_id: str) -> Response:
    return api_identifier_crud.get_model(db, Response, api_id=response_api_id)


def get_responses(
    db: Session, letter: Letter, response_api_ids: list[str]
) -> list[Response]:
    responses = api_identifier_crud.get_models(db, Response, response_api_ids)
    assert all(response.question.letter_id == letter.id for response in responses)
    return responses


def edit_responses(
    response_map: dict[str, Response],
    updated_responses: Sequence[ResponseUpdate],
) -> list[Response]:
    for updated_resp in updated_responses:
        db_response = response_map[updated_resp.api_identifier]
        db_response.response_text = updated_resp.response_text
    return list(response_map.values())
