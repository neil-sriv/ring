from typing import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from llm.config import get_config
from llm.lib.logger import logger
from llm.routes import router

llm_config = get_config()
app = FastAPI(root_path=llm_config.root_path)

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