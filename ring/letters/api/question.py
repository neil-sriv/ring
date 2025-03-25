from __future__ import annotations

from fastapi import APIRouter, Depends, UploadFile

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

    :param question_api_id: API identifier of the question
    :type question_api_id: str
    :param response: Response creation/update parameters
    :type response: ResponseUpsert
    :param req_dep: Request dependencies including database session and auth
    :type req_dep: AuthenticatedRequestDependencies
    :raises IDNotFoundException: If question or response with given API ID is not found
    :return: Updated question with the new/updated response
    :rtype: Question
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

    :param question_api_id: API identifier of the question
    :type question_api_id: str
    :param response_image: Image file to upload
    :type response_image: UploadFile
    :param req_dep: Request dependencies including database session and auth
    :type req_dep: AuthenticatedRequestDependencies
    :raises IDNotFoundException: If question with given API ID is not found
    :return: Updated question with the response containing the new image
    :rtype: Question
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
