"""Question API endpoints.

This module provides FastAPI endpoints for managing question responses, including
creating, updating, and uploading images for responses.
"""

from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from loguru import logger

from ring.authz.authz import load_and_check
from ring.authz.enforcer import Action
from ring.fastapp.dependencies import (
    AuthenticatedRequestDependencies,
    get_request_dependencies,
)
from ring.letters.constants import LetterStatus
from ring.letters.crud import question as question_crud
from ring.letters.crud.response import upload_image as upload_image_crud
from ring.letters.models.question_model import Question
from ring.letters.models.response_model import Response
from ring.letters.schemas.response import ResponseUpsert
from ring.ring_pydantic.linked_schemas import QuestionLinked

router = APIRouter()

_DIFFERENT_PARTICIPANT = "Cannot write a response as a different participant"
_WRONG_QUESTION = "Response does not belong to this question"


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
    """Create or update the caller's response to a question.

    The participant is always the signed-in caller. A
    ``participant_api_identifier`` that names someone else is rejected,
    including for a group admin. An ``api_identifier`` edits that response
    only when the caller owns it and it belongs to this question. With no
    ``api_identifier``, the caller's response on this question is updated,
    or created.

    Admins change another member's answer through
    ``POST /responses/response/{response_api_id}:edit_response``.

    Args:
        question_api_id (str): API identifier of the question
        response (ResponseUpsert): Response creation/update parameters
        req_dep (AuthenticatedRequestDependencies): Request dependencies including database session and auth

    Returns:
        Question: Updated question with the new/updated response

    Raises:
        PermissionError: If the caller cannot read the question or response
        HTTPException: If the body names another participant, the caller
            does not own the response, or the response is on another question
    """
    logger.info(response)
    caller = req_dep.current_user
    # Field is deprecated; reading the attribute warns on every call.
    payload = response.model_dump(warnings=False)
    participant_api_identifier = payload["participant_api_identifier"]
    api_identifier = payload["api_identifier"]
    db_question = cast(
        Question,
        load_and_check(
            req_dep.db,
            caller,
            Action.READ,
            question_api_id,
        ),
    )
    if (
        participant_api_identifier is not None
        and participant_api_identifier != caller.api_identifier
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=_DIFFERENT_PARTICIPANT,
        )
    if api_identifier:
        db_response = cast(
            Response,
            load_and_check(
                req_dep.db,
                caller,
                Action.READ,
                api_identifier,
            ),
        )
        if db_response.participant.api_identifier != caller.api_identifier:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=_DIFFERENT_PARTICIPANT,
            )
        if db_response.question.api_identifier != db_question.api_identifier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_WRONG_QUESTION,
            )
        question_crud.edit_response(
            req_dep.db,
            db_response,
            response.response_text,
        )
    else:
        existing = next(
            (
                resp
                for resp in db_question.responses
                if resp.participant.api_identifier == caller.api_identifier
            ),
            None,
        )
        if existing is not None:
            question_crud.edit_response(
                req_dep.db,
                existing,
                response.response_text,
            )
        else:
            question_crud.add_response(
                req_dep.db,
                db_question,
                caller,
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
        PermissionError: If the caller is not a member of the question's group
        IDNotFoundException: If question with given API ID is not found
    """
    db_question = cast(
        Question,
        load_and_check(
            req_dep.db,
            req_dep.current_user,
            Action.READ,
            question_api_id,
        ),
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
    await upload_image_crud(
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
    Questions with responses cannot be deleted. A sent loop is frozen;
    upcoming and in-progress loops still allow deletion when the
    question has no responses.

    Args:
        question_api_id (str): API identifier of the question to delete
        req_dep (AuthenticatedRequestDependencies): Request dependencies including database session and auth

    Raises:
        PermissionError: If the caller is not a member of the question's group
        HTTPException: If user not authorized, question has responses, or
            the loop has been sent
    """
    db_question = cast(
        Question,
        load_and_check(
            req_dep.db,
            req_dep.current_user,
            Action.READ,
            question_api_id,
        ),
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

    # Sent loops are frozen. Upcoming and in-progress loops can still
    # drop a question that nobody has answered.
    if db_question.letter.status == LetterStatus.SENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a question from a loop that has been sent",
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


# @router.post(
#     "/question:generate",
#     response_model=GenerateQuestionResponse,
# )
# async def generate_question(
#     request: GenerateQuestionRequest,
#     req_dep: AuthenticatedRequestDependencies = Depends(
#         get_request_dependencies,
#     ),
# ) -> GenerateQuestionResponse:
#     """Generate a question using LLM without saving it."""
#     generated_text = question_crud.generate_question(request.prompt, letter)
#     return GenerateQuestionResponse(generated_text=generated_text)
