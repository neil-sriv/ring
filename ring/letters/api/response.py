"""Response API endpoints.

This module provides FastAPI endpoints for managing responses, including editing
response text and uploading images. Note that the image upload endpoint is
deprecated in favor of the question-level image upload endpoint.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, UploadFile

from ring.api_identifier import (
    util as api_identifier_crud,
)
from ring.fastapp.dependencies import (
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
    """Update the text content of a response.

    Args:
        response_api_id (str): API identifier of the response to edit
        response (ResponseCreateBase): Updated response content
        req_dep (AuthenticatedRequestDependencies): Request dependencies including database session and auth

    Returns:
        Response: Updated response

    Raises:
        IDNotFoundException: If response with given API ID is not found
    """
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
    """Upload images to attach to a response.

    This endpoint is deprecated. Use the question-level image upload endpoint instead.

    Args:
        response_api_id (str): API identifier of the response
        response_images (list[UploadFile]): List of image files to upload
        req_dep (AuthenticatedRequestDependencies): Request dependencies including database session and auth

    Returns:
        Response: Updated response with attached images

    Raises:
        IDNotFoundException: If response with given API ID is not found
    """
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
