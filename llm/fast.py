from __future__ import annotations

from typing import Awaitable, Callable

from fastapi import Depends, FastAPI, Request, Response

from llm.config import get_config
from llm.lib.logger import logger
from llm.routes import router
from llm.security.security import get_api_key

llm_config = get_config()
app = FastAPI(
    root_path=llm_config.root_path,
    dependencies=[Depends(get_api_key)],
    version="0.2.0",
)

app.include_router(router)


@app.middleware("http")
async def log_requests(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response
