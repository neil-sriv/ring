"""Document API endpoints.

This module provides FastAPI endpoints for managing documents, including
creating, updating, deleting documents and managing document edits.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, WebSocket, status
from loguru import logger
from pycrdt import Doc, Provider
from pycrdt.websocket import WebsocketServer
from starlette.websockets import WebSocketDisconnect

from ring.api_identifier.util import get_model
from ring.fastapp.dependencies import (
    AuthenticatedRequestDependencies,
    RequestDependenciesBase,
    get_request_dependencies,
    get_unauthenticated_request_dependencies,
    get_websocket_request_dependencies,
)
from ring.notebook.crud.document import (
    add_document_edit,
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
    logger.info(f"Creating document: {document.name}")
    db_document = create_document(
        req_dep.db,
        document.name,
        document.content,
        req_dep.current_user,
    )
    req_dep.db.commit()
    return db_document


@router.get(
    "/documents/{group_api_id}",
    response_model=List[DocumentResponse],
)
async def list_documents(
    group_api_id: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> List[Document]:
    """List documents for a group.

    Args:
        group_api_id (str): API identifier of the group
        req_dep (AuthenticatedRequestDependencies): Request dependencies including database session and auth

    Returns:
        List[Document]: List of documents
    """
    documents = get_documents(req_dep.db, group_api_id)
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

    # Check if user is authorized to update the document
    # For now, allow any authenticated user to update any document
    # You can add more sophisticated authorization logic here

    updated_document = update_document(
        req_dep.db,
        db_document,
        name=document_update.name,
        content=document_update.content,
    )

    req_dep.db.commit()
    return updated_document


# @websocket_router.websocket("/{document_api_id}")
# async def nb_document_websocket(
#     websocket: WebSocket,
#     document_api_id: str,
#     req_dep: AuthenticatedRequestDependencies = Depends(
#         get_websocket_request_dependencies
#     ),
# ) -> None:
#     """
#     Websocket endpoint for a notebook document.
#     """
#     logger.info(f"WebSocket request for document {document_api_id}")
#     db_document = get_model(req_dep.db, Document, document_api_id)
#     await websocket.accept()
#     logger.info(
#         f"WebSocket connected to document {document_api_id} by user {req_dep.current_user.email}"
#     )
#     await join_document_room(document_api_id, websocket)
#     try:
#         while True:
#             data = await websocket.receive_bytes()
#             logger.info(f"Received data: {data}")
#             print(data)
#             # db_edit = add_document_edit(
#             #     req_dep.db,
#             #     db_document,
#             #     data,
#             #     req_dep.current_user,
#             # )
#             # req_dep.db.commit()
#             await broadcast_document_message(document_api_id, data, websocket)
#     except WebSocketDisconnect:
#         logger.info(f"Client disconnected from document {document_api_id}")
#         await leave_document_room(document_api_id, websocket)
#     except Exception as e:
#         logger.error(f"WebSocket error: {e}")
#         await leave_document_room(document_api_id, websocket)
#         try:
#             await websocket.close()
#         except RuntimeError:
#             pass
#         raise
