from __future__ import annotations

from fastapi import APIRouter, Depends, UploadFile

from ring.api_identifier import (
    util as api_identifier_crud,
)
from ring.dependencies import (
    AuthenticatedRequestDependencies,
    get_request_dependencies,
)
from ring.letters.crud import (
    question as question_crud,
)
from ring.letters.crud import (
    response as response_crud,
)
from ring.letters.models.response_model import Response
from ring.letters.schemas.response import ResponseCreateBase
from ring.ring_pydantic.linked_schemas import ResponseLinked

router = APIRouter()


@router.post(
    "/response/{response_api_id}:edit_response",
    response_model=ResponseLinked,
)
async def edit_response(
    response_api_id: str,
    response: ResponseCreateBase,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Response:
    update_response = api_identifier_crud.get_model(
        req_dep.db, Response, api_id=response_api_id
    )
    question_crud.edit_response(
        req_dep.db,
        update_response,
        response.response_text,
    )
    req_dep.db.commit()
    return update_response


@router.post(
    "/response/{response_api_id}:upload_image",
    response_model=ResponseLinked,
    deprecated=True,
)
async def upload_image(
    response_api_id: str,
    response_images: list[UploadFile],
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Response:
    update_response = api_identifier_crud.get_model(
        req_dep.db, Response, api_id=response_api_id
    )
    await response_crud.a_upload_image(
        req_dep.db,
        update_response,
        response_images,
    )
    req_dep.db.commit()
    return update_response
