from typing import Awaitable, Callable, TypeVar

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from ring.api_identifier.util import IDNotFoundException
from ring.config import get_config
from ring.lib.logger import logger
from ring.routes import router

ring_config = get_config()
app = FastAPI(root_path=ring_config.root_path)

if ring_config.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(origin).strip("/")
            for origin in ring_config.BACKEND_CORS_ORIGINS
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(router)


@app.exception_handler(IDNotFoundException)
async def id_not_found_exception_handler(
    request: Request, exc: IDNotFoundException
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "detail": "Model ids not found",
            "model": exc.model_cls.__name__,
            "api_ids": exc.api_ids,
        },
    )


@app.middleware("http")
async def log_requests(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response
