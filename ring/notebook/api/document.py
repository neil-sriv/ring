"""Document API endpoints.

This module provides FastAPI endpoints for managing documents, including
creating, updating, deleting documents and managing document edits.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, WebSocket, status
from loguru import logger
from starlette.websockets import WebSocketDisconnect

from ring.api_identifier.util import get_model
from ring.fastapp.dependencies import (
    AuthenticatedRequestDependencies,
    get_request_dependencies,
    get_websocket_request_dependencies,
)
from ring.notebook.crud.document import (
    broadcast_document_message,
    create_document,
    get_documents,
    join_document_room,
    leave_document_room,
    update_document,
)
from ring.notebook.models.document import Document
from ring.notebook.schemas.document import (
    DocumentCreate,
    DocumentResponse,
    DocumentUpdate,
)
from ring.parties.models.group_model import Group

router = APIRouter()
websocket_router = APIRouter()


@router.post(
    "/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_document_endpoint(
    document: DocumentCreate,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Document:
    """Create a new document.

    Args:
        document (DocumentCreate): Document creation parameters
        req_dep (AuthenticatedRequestDependencies): Request dependencies including database session and auth

    Returns:
        Document: Newly created document
    """
    group = get_model(req_dep.db, Group, document.group_api_id)
    db_document = create_document(
        req_dep.db,
        document.name,
        document.content,
        req_dep.current_user,
        group,
    )
    req_dep.db.commit()
    return db_document


@router.get(
    "/documents",
    response_model=list[DocumentResponse],
)
async def list_documents(
    group_api_id: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> list[Document]:
    """List documents for a group.

    Args:
        group_api_id (str): API identifier of the group
        req_dep (AuthenticatedRequestDependencies): Request dependencies including database session and auth

    Returns:
        List[Document]: List of documents
    """
    group = get_model(req_dep.db, Group, group_api_id)
    documents = get_documents(req_dep.db, group)
    return documents


@router.get(
    "/documents/{document_api_id}",
    response_model=DocumentResponse,
)
async def get_document_endpoint(
    document_api_id: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Document:
    """Get a document by its API identifier.

    Args:
        document_api_id (str): API identifier of the document
        req_dep (AuthenticatedRequestDependencies): Request dependencies including database session and auth

    Returns:
        Document: The requested document

    Raises:
        IDNotFoundException: If document with given API ID is not found
    """
    return get_model(req_dep.db, Document, document_api_id)


@router.put(
    "/documents/{document_api_id}",
    response_model=DocumentResponse,
)
async def update_document_endpoint(
    document_api_id: str,
    document_update: DocumentUpdate,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> Document:
    """Update a document.

    Args:
        document_api_id (str): API identifier of the document
        document_update (DocumentUpdate): Document update parameters
        req_dep (AuthenticatedRequestDependencies): Request dependencies including database session and auth

    Returns:
        Document: Updated document

    Raises:
        IDNotFoundException: If document with given API ID is not found
    """
    db_document = get_model(req_dep.db, Document, document_api_id)

    updated_document = update_document(
        req_dep.db,
        db_document,
        name=document_update.name,
        content=document_update.content,
    )

    req_dep.db.commit()
    return updated_document


@websocket_router.websocket("/")
async def nb_automerge_repo_websocket(
    websocket: WebSocket,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_websocket_request_dependencies
    ),
) -> None:
    """
    WebSocket endpoint for Automerge Repo collaboration.
    This endpoint handles Automerge sync protocol messages.
    """
    await websocket.accept()

    # Store active connections for broadcasting
    active_automerge_connections = getattr(
        nb_automerge_repo_websocket, "active_connections", set()
    )
    active_automerge_connections.add(websocket)
    nb_automerge_repo_websocket.active_connections = (
        active_automerge_connections
    )

    try:
        while True:
            data = await websocket.receive_text()

            # Parse JSON message
            try:
                import json

                message = json.loads(data)

                if message.get("type") == "content_update":
                    # Broadcast content update to all other clients
                    for connection in active_automerge_connections:
                        if connection != websocket:
                            try:
                                await connection.send_text(data)
                            except Exception:
                                # Remove dead connections
                                active_automerge_connections.discard(
                                    connection
                                )

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data}")

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"Automerge WebSocket error: {e}")
        try:
            await websocket.close()
        except RuntimeError:
            pass
        raise
    finally:
        # Clean up connection
        active_automerge_connections.discard(websocket)


@websocket_router.websocket("/{document_api_id}")
async def nb_document_websocket(
    websocket: WebSocket,
    document_api_id: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_websocket_request_dependencies
    ),
) -> None:
    """
    Websocket endpoint for a notebook document.
    """
    db_document = get_model(req_dep.db, Document, document_api_id)
    await websocket.accept()
    await join_document_room(document_api_id, websocket)
    try:
        while True:
            message = await websocket.receive()

            # Handle different message types
            if message["type"] == "websocket.receive":
                if "bytes" in message:
                    data = message["bytes"]
                    await broadcast_document_message(
                        document_api_id, data, websocket
                    )
                elif "text" in message:
                    data = message["text"].encode("utf-8")
                    await broadcast_document_message(
                        document_api_id, data, websocket
                    )
                else:
                    logger.warning(f"Unknown message format: {message}")
            elif message["type"] == "websocket.disconnect":
                logger.info("WebSocket disconnected")
                break
    except WebSocketDisconnect:
        await leave_document_room(document_api_id, websocket)
    except Exception as e:
        logger.error(f"Document WebSocket error: {e}")
        await leave_document_room(document_api_id, websocket)
        try:
            await websocket.close()
        except RuntimeError:
            pass
        raise
