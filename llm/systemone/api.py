from __future__ import annotations

from fastapi import APIRouter, HTTPException

from llm.lib.logger import logger
from llm.systemone.evaluate import SystemOneError, evaluate
from llm.systemone.schemas import SystemOneRequest, SystemOneResponse

router = APIRouter()


@router.post(
    "/systemone",
    response_model=SystemOneResponse,
    summary="System One decisions (Jev spike)",
)
async def evaluate_systemone(request: SystemOneRequest) -> SystemOneResponse:
    """Evaluate state with Choice, Score, and Noul questions.

    Spike: proxies to TypeSafe when JEV_API_KEY is set, otherwise wraps the
    existing chat-completion client in the public System One response shape.
    """
    logger.info("systemone questions=%s", len(request.questions))
    try:
        return await evaluate(request)
    except SystemOneError as exc:
        raise HTTPException(
            status_code=exc.status_code, detail=exc.detail
        ) from exc
