"""FastAPI application entry point for Ring.

This module sets up the FastAPI application with CORS middleware, exception handlers,
and request logging. It serves as the main entry point for the Ring API service.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.cors import CORSMiddleware

from ring.api_identifier.util import IDNotFoundException
from ring.async_scheduler.scheduler import scheduler
from ring.fastapp.config import get_config
from ring.fastapp.init_app_modules import init_app_modules
from ring.fastapp.routes import router
from ring.lib.request_logging import (
    install_uvicorn_access_log_redaction,
    sanitize_request_url,
)
from ring.notebook.sync import notebook_websocket_server
from ring.sqlalchemy_base import SessionLocal
from ring.tasks.crud import task as task_crud


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Uvicorn may create its access logger after import; ensure the filter is on.
    install_uvicorn_access_log_redaction()

    ring_config = get_config()
    if not ring_config.DISABLE_SCHEDULER:
        # The jobstore was wiped when the app modules initialized, so any
        # task still IN_PROGRESS was stranded by the previous process and
        # must go back to PENDING before the poll loop starts.
        with SessionLocal() as db:
            requeued = task_crud.requeue_in_progress_tasks(db)
            if requeued:
                logger.info(
                    "Requeued {} task(s) stranded in progress by the "
                    "previous process".format(requeued)
                )
        scheduler.start()

    # Runs the notebook CRDT rooms' task group for the app's lifetime.
    async with notebook_websocket_server:
        yield

    if not ring_config.DISABLE_SCHEDULER:
        scheduler.shutdown()


def create_app() -> FastAPI:
    install_uvicorn_access_log_redaction()

    ring_config = get_config()
    app = FastAPI(root_path=ring_config.root_path, lifespan=lifespan)

    init_app_modules()

    if (
        ring_config.BACKEND_CORS_ORIGINS
        or ring_config.BACKEND_CORS_ORIGIN_REGEX
    ):
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                str(origin).strip("/")
                for origin in ring_config.BACKEND_CORS_ORIGINS
            ],
            allow_origin_regex=ring_config.BACKEND_CORS_ORIGIN_REGEX or None,
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


@app.exception_handler(PermissionError)
async def permission_error_handler(
    request: Request, exc: PermissionError
) -> JSONResponse:
    """Map authz PermissionError to a 403 response.

    Raised by ring.authz helpers; also covers resources whose ids do not
    resolve, so unauthorized users cannot probe for resource existence.
    """
    return JSONResponse(
        status_code=403,
        content={"detail": "Not authorized to access this resource"},
    )


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
    and the status code for each response. Sensitive path/query values
    (invite tokens, password-reset tokens, JWT query params) are redacted.

    Args:
        request (Request): The incoming HTTP request
        call_next (Callable[[Request], Awaitable[Response]]): Function to call the next middleware or route handler

    Returns:
        Response: The HTTP response
    """
    safe_url = sanitize_request_url(str(request.url))
    logger.info(f"Request: {request.method} {safe_url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response
