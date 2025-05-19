"""FastAPI application entry point for Ring.

This module sets up the FastAPI application with CORS middleware, exception handlers,
and request logging. It serves as the main entry point for the Ring API service.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from ring.api_identifier.util import IDNotFoundException
from ring.async_scheduler.scheduler import scheduler
from ring.fastapp.config import get_config
from ring.fastapp.init_app_modules import init_app_modules
from ring.fastapp.routes import router
from ring.lib.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown()


def create_app() -> FastAPI:
    ring_config = get_config()
    app = FastAPI(root_path=ring_config.root_path, lifespan=lifespan)

    init_app_modules()

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

    return app


app = create_app()


# @app.on_event("startup")
# async def startup_event():
#     scheduler.start()


@app.exception_handler(IDNotFoundException)
async def id_not_found_exception_handler(
    request: Request, exc: IDNotFoundException
) -> JSONResponse:
    """Handle exceptions when API identifiers are not found.

    Args:
        request (Request): The incoming HTTP request
        exc (IDNotFoundException): The exception containing details about missing identifiers

    Returns:
        JSONResponse: A 404 response with details about the missing identifiers
    """
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
    """Log HTTP request and response details.

    This middleware logs the HTTP method and URL for each request,
    and the status code for each response.

    Args:
        request (Request): The incoming HTTP request
        call_next (Callable[[Request], Awaitable[Response]]): Function to call the next middleware or route handler

    Returns:
        Response: The HTTP response
    """
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response
