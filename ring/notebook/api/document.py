from __future__ import annotations

from fastapi import APIRouter, Depends, WebSocket
from fastapi.responses import HTMLResponse

from ring.fastapp.dependencies import (
    AuthenticatedRequestDependencies,
    get_request_dependencies,
)

router = APIRouter()


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
            var ws = new WebSocket("wss://localhost/api/v1/notebook/ws/notebook/123");
            
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


@router.websocket("/ws/notebook/{document_api_id}")
async def nb_document_websocket(
    websocket: WebSocket,
    document_api_id: str,
    # req_dep: AuthenticatedRequestDependencies = Depends(
    #     get_request_dependencies,
    # ),
) -> None:
    """
    Websocket endpoint for a notebook document.
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()
