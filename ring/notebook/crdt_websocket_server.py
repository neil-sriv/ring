from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from loguru import logger
from pycrdt import Doc
from pycrdt.websocket import ASGIServer, WebsocketServer

from ring.notebook.custom_provider import CustomProvider
from ring.notebook.sqlalchemy_store import SQLAlchemyStore
from ring.parties.models.user_model import User
from ring.sqlalchemy_base import get_db


def create_websocket_server() -> WebsocketServer:
    def exception_handler(exception: Exception, logger) -> bool:
        error_types = [
            "ClientDisconnected",
            "ConnectionClosedError",
            "IncompleteReadError",
            "no close frame received or sent",
            "Awareness not started",
            "Unexpected ASGI message",
            "after sending 'websocket.close'",
        ]
        if any(error_type in str(exception) for error_type in error_types):
            return True
        return False

    def provider_factory(doc: Doc, log=None, path: str = None):
        @asynccontextmanager
        async def provider_context():
            db = next(get_db())
            try:
                document_id = path.split("/")[-1] if path else "default"
                user = db.query(User).order_by(User.id).first()
                store = SQLAlchemyStore(
                    db=db, document_api_id=document_id, user=user
                )

                class MinimalChannel:
                    def __init__(self, path: str):
                        self._path = path

                    @property
                    def path(self) -> str:
                        return self._path

                    async def send(self, message: bytes) -> None:
                        pass

                    async def recv(self) -> bytes:
                        return b""

                    def __aiter__(self):
                        return self

                    async def __anext__(self):
                        raise StopAsyncIteration()

                channel = MinimalChannel(document_id)
                provider = CustomProvider(
                    doc=doc, channel=channel, store=store, log=log
                )
                await provider.initialize()
                await provider.start()

                try:
                    yield provider
                finally:
                    try:
                        await provider.stop()
                    except Exception:
                        pass
            except Exception as e:
                if any(
                    error_type in str(e)
                    for error_type in [
                        "ClientDisconnected",
                        "ConnectionClosedError",
                        "IncompleteReadError",
                        "no close frame received or sent",
                    ]
                ):
                    return
                raise

        return provider_context()

    return WebsocketServer(
        provider_factory=provider_factory, exception_handler=exception_handler
    )


class ErrorHandlingASGIServer:
    def __init__(self, websocket_server: WebsocketServer):
        self._ws_server = websocket_server
        self._asgi_server = ASGIServer(websocket_server)

    async def __call__(self, scope: dict[str, Any], receive, send):
        try:
            await self._asgi_server(scope, receive, send)
        except Exception as e:
            error_types = [
                "ClientDisconnected",
                "ConnectionClosedError",
                "IncompleteReadError",
                "no close frame received or sent",
                "Awareness not started",
                "Unexpected ASGI message",
                "after sending 'websocket.close'",
            ]
            if any(error_type in str(e) for error_type in error_types):
                return
            if "The WebsocketServer is not running" in str(e):
                try:
                    await self._ws_server.stop()
                except:
                    pass
                await self._ws_server.start()
                await self._asgi_server(scope, receive, send)
                return
            raise


def create_asgi_server(
    websocket_server: WebsocketServer,
) -> ErrorHandlingASGIServer:
    return ErrorHandlingASGIServer(websocket_server)
