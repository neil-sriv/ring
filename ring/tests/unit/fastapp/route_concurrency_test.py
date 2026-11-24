"""Guard against sync I/O blocking FastAPI's single asyncio event loop."""

from __future__ import annotations

import ast
import inspect
import textwrap

from fastapi.routing import APIRoute

from ring.fastapp import dependencies
from ring.fastapp.fast import app
from ring.letters.crud import response as response_crud

# Pure-Python no-I/O health checks that do not need threadpool dispatch.
_NO_IO_ASYNC_ENDPOINTS = {"root", "hello"}


def _contains_async_suspension(func: object) -> bool:
    source = textwrap.dedent(inspect.getsource(func))  # type: ignore[arg-type]
    tree = ast.parse(source)
    return any(
        isinstance(node, (ast.Await, ast.AsyncWith, ast.AsyncFor))
        for node in ast.walk(tree)
    )


def test_async_http_routes_actually_await() -> None:
    """Every ``async def`` HTTP route must either await or perform no I/O.

    Ring uses synchronous SQLAlchemy and boto3 inside a single uvicorn worker.
    Declaring a sync route as ``async def`` bypasses FastAPI's worker
    threadpool and stalls the event loop (including notebook WebSockets).
    """
    offenders: list[str] = []
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        endpoint = route.endpoint
        if not endpoint.__module__.startswith("ring."):
            continue
        if not inspect.iscoroutinefunction(endpoint):
            continue
        if endpoint.__name__ in _NO_IO_ASYNC_ENDPOINTS:
            continue
        if not _contains_async_suspension(endpoint):
            offenders.append(
                f"{endpoint.__module__}.{endpoint.__name__} ({route.path})"
            )

    assert offenders == [], (
        "HTTP routes declared `async def` without awaiting run on the main "
        "event loop and block sync I/O; use `def` instead: "
        + ", ".join(offenders)
    )


def test_sync_dependencies_and_s3_upload_are_not_coroutines() -> None:
    """Dependencies using sync SQLAlchemy/boto3 must be plain ``def``."""
    sync_callables = [
        dependencies.get_current_user,
        dependencies.get_request_dependencies,
        dependencies.get_unauthenticated_request_dependencies,
        dependencies.get_websocket_request_dependencies,
        dependencies.get_s3_client_dependencies,
        response_crud.upload_image,
    ]
    for fn in sync_callables:
        assert not inspect.iscoroutinefunction(
            fn
        ), f"{fn.__module__}.{fn.__name__} must be `def`, not `async def`"
