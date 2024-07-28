from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile
from ring.dependencies import (
    AuthenticatedRequestDependencies,
    get_request_dependencies,
)
from ring.api_identifier import (
    util as api_identifier_crud,
)
from ring.letters.crud import question as question_crud
from ring.letters.models.question_model import Question
from ring.letters.models.response_model import Response
from ring.ring_pydantic.linked_schemas import QuestionLinked
from ring.letters.schemas.response import ResponseUpsert
from ring.letters.crud.response import a_upload_image

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
        [db_response] = [resp for resp in db_question.responses if resp.participant.api_identifier == response.participant_api_identifier]
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
    db_question = api_identifier_crud.get_model(
        req_dep.db, Question, api_id=question_api_id
    )
    response = [resp for resp in db_question.responses if resp.participant.api_identifier == req_dep.current_user.api_identifier]
    if response:
        db_response = response[0]
    else:
        db_response = question_crud.add_response(
            req_dep.db,
            db_question,
            req_dep.current_user,
            ""
        )
    await a_upload_image(
            req_dep.db,
            db_response,
            [response_image],
        )
    req_dep.db.commit()
    return db_question
