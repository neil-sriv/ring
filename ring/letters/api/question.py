"""Question API endpoints.

This module provides FastAPI endpoints for managing question responses, including
creating, updating, and uploading images for responses.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from ring.api_identifier import (
    util as api_identifier_crud,
)
from ring.dependencies import (
    AuthenticatedRequestDependencies,
    get_request_dependencies,
)
from ring.letters.crud import question as question_crud
from ring.letters.crud.response import a_upload_image
from ring.letters.models.question_model import Question
from ring.letters.models.response_model import Response
from ring.letters.schemas.response import ResponseUpsert
from ring.ring_pydantic.linked_schemas import QuestionLinked

router = APIRouter()


@router.post(
    "/question/{question_api_id}:upsert_response",
    response_model=QuestionLinked,
)
async def upsert_response(
    question_api_id: str,
    response: ResponseUpsert,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Question:
    """Create or update a response to a question.

    If a response already exists (identified by api_identifier or participant),
    updates it. Otherwise, creates a new response.

    Args:
        question_api_id (str): API identifier of the question
        response (ResponseUpsert): Response creation/update parameters
        req_dep (AuthenticatedRequestDependencies): Request dependencies including database session and auth

    Returns:
        Question: Updated question with the new/updated response

    Raises:
        IDNotFoundException: If question or response with given API ID is not found
    """
    print(response)
    db_question = api_identifier_crud.get_model(
        req_dep.db, Question, api_id=question_api_id
    )
    if response.api_identifier:
        db_response = api_identifier_crud.get_model(
            req_dep.db, Response, api_id=response.api_identifier
        )
        question_crud.edit_response(
            req_dep.db,
            db_response,
            response.response_text,
        )
    elif response.participant_api_identifier:
        db_responses = [
            resp
            for resp in db_question.responses
            if resp.participant.api_identifier
            == response.participant_api_identifier
        ]
        if db_responses:
            db_response = db_responses[0]
            question_crud.edit_response(
                req_dep.db,
                db_response,
                response.response_text,
            )
        else:
            db_response = question_crud.add_response(
                req_dep.db,
                db_question,
                req_dep.current_user,
                response.response_text,
            )
    req_dep.db.commit()
    return db_question


@router.post(
    "/question/{question_api_id}:upload_image",
    response_model=QuestionLinked,
)
async def upload_image(
    question_api_id: str,
    response_image: UploadFile,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Question:
    """Upload an image as part of a response to a question.

    Creates a new response if one doesn't exist for the current user,
    then attaches the uploaded image to it.

    Args:
        question_api_id (str): API identifier of the question
        response_image (UploadFile): Image file to upload
        req_dep (AuthenticatedRequestDependencies): Request dependencies including database session and auth

    Returns:
        Question: Updated question with the response containing the new image

    Raises:
        IDNotFoundException: If question with given API ID is not found
    """
    db_question = api_identifier_crud.get_model(
        req_dep.db, Question, api_id=question_api_id
    )
    response = [
        resp
        for resp in db_question.responses
        if resp.participant.api_identifier
        == req_dep.current_user.api_identifier
    ]
    if response:
        db_response = response[0]
    else:
        db_response = question_crud.add_response(
            req_dep.db, db_question, req_dep.current_user, ""
        )
    await a_upload_image(
        req_dep.db,
        db_response,
        [response_image],
    )
    req_dep.db.commit()
    return db_question


@router.delete(
    "/question/{question_api_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_question(
    question_api_id: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> None:
    """Delete a question.

    Only the question author or group admin can delete a question.
    Questions with responses cannot be deleted.
    
    Args:
        question_api_id (str): API identifier of the question to delete
        req_dep (AuthenticatedRequestDependencies): Request dependencies including database session and auth

    Raises:
        HTTPException: If question not found, user not authorized, or question has responses
    """
    db_question = api_identifier_crud.get_model(
        req_dep.db, Question, api_id=question_api_id
    )

    # Check if user is authorized to delete the question
    if (
        req_dep.current_user != db_question.author
        and req_dep.current_user != db_question.letter.group.admin
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the question author or group admin can delete a question",
        )

    try:
        question_crud.delete_question(
            req_dep.db,
            db_question,
        )
        req_dep.db.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
