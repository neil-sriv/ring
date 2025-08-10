from __future__ import annotations

from dataclasses import dataclass, field

from fastapi import WebSocket
from loguru import logger

active_connections: dict[str, DocumentRoom] = {}


@dataclass
class DocumentRoom:
    """
    A room for a document.
    """

    document_api_id: str
    active_connections: list[WebSocket] = field(default_factory=list)


async def join_document_room(
    document_api_id: str,
    websocket: WebSocket,
) -> None:
    """
    Join a document room.
    """
    room = active_connections.get(document_api_id)
    if not room:
        room = DocumentRoom(document_api_id=document_api_id)
    room.active_connections.append(websocket)
    logger.debug(f"{room}")
    active_connections[document_api_id] = room


async def leave_document_room(
    document_api_id: str,
    websocket: WebSocket,
) -> None:
    """
    Leave a document room.
    """
    room = active_connections.get(document_api_id)
    if not room:
        return
    room.active_connections.remove(websocket)
    logger.debug(f"{room}")
    if not room.active_connections:
        del active_connections[document_api_id]


async def broadcast_document_message(
    document_api_id: str,
    data: bytes,
    sender: WebSocket,
) -> None:
    """
    Broadcast a message to all connections in a document room.
    """
    room = active_connections.get(document_api_id)
    if not room:
        return
    for connection in room.active_connections:
        logger.debug(f"{connection}")
        if connection == sender:
            continue
        await connection.send_bytes(data)
