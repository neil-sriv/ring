from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from httpx_ws import aconnect_ws
from loguru import logger
from pycrdt import Channel, Doc, Provider
from pycrdt.websocket import ASGIServer, WebsocketServer


@asynccontextmanager
async def get_provider(path: str, doc: Doc, log=None) -> Provider:
    logger.info(f"Creating provider with path: {path}")
    connect = aconnect_ws(f"http://localhost/{path}")
    async with connect as websocket:
        provider = Provider(doc=doc, channel=websocket, log=log)
        yield provider


def create_websocket_server() -> WebsocketServer:
    return WebsocketServer(provider_factory=get_provider)


def create_asgi_server(websocket_server: WebsocketServer) -> ASGIServer:
    return ASGIServer(websocket_server)
