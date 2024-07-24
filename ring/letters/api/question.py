from __future__ import annotations
from fastapi import APIRouter, Depends
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
    question = api_identifier_crud.get_model(
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
    else:
        question_crud.add_response(
            req_dep.db,
            question,
            req_dep.current_user,
            response.response_text,
        )
    req_dep.db.commit()
    return question
