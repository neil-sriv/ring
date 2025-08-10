from __future__ import annotations

from fastapi import APIRouter, Depends, WebSocket
from fastapi.responses import HTMLResponse
from loguru import logger
from starlette.websockets import WebSocketDisconnect

from ring.fastapp.dependencies import (
    AuthenticatedRequestDependencies,
    RequestDependenciesBase,
    get_request_dependencies,
    get_unauthenticated_request_dependencies,
)
from ring.notebook.crud.document import (
    broadcast_document_message,
    join_document_room,
    leave_document_room,
)

router = APIRouter()
websocket_router = APIRouter()


html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("wss://localhost/api/v1/ws/notebook/123");
            
            ws.onopen = function(event) {
                console.log("WebSocket connection established");
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode("Connected to WebSocket")
                message.appendChild(content)
                messages.appendChild(message)
            };
            
            ws.onerror = function(error) {
                console.error("WebSocket error:", error);
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode("WebSocket error: " + error)
                message.appendChild(content)
                messages.appendChild(message)
            };
            
            ws.onclose = function(event) {
                console.log("WebSocket connection closed:", event.code, event.reason);
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode("WebSocket connection closed")
                message.appendChild(content)
                messages.appendChild(message)
            };
            
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


@router.get("/")
async def get():
    return HTMLResponse(html)


@websocket_router.websocket("/{document_api_id}")
async def nb_document_websocket(
    websocket: WebSocket,
    document_api_id: str,
    req_dep: RequestDependenciesBase = Depends(
        get_unauthenticated_request_dependencies
    ),
) -> None:
    """
    Websocket endpoint for a notebook document.
    """
    await websocket.accept()
    await join_document_room(document_api_id, websocket)
    try:
        while True:
            # data = await websocket.receive_bytes()
            data = await websocket.receive_text()
            await broadcast_document_message(document_api_id, data, websocket)
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        # Client disconnected normally - just clean up
        logger.info(f"Client disconnected from document {document_api_id}")
        await leave_document_room(document_api_id, websocket)
        # Don't try to close - it's already closed
    except Exception as e:
        # Handle other unexpected errors
        logger.error(f"WebSocket error: {e}")
        await leave_document_room(document_api_id, websocket)
        try:
            await websocket.close()
        except RuntimeError:
            # WebSocket already closed, ignore
            pass
        raise
