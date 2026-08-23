"""Document API endpoints.

This module provides FastAPI endpoints for managing documents (create, list,
read, update) and the Yjs CRDT synchronization WebSocket used by the
collaborative editor.
"""

from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Depends, WebSocket, status
from pycrdt.websocket.websocket import HttpxWebsocket

from ring.api_identifier.util import IDNotFoundException
from ring.authz.authz import load_and_check
from ring.authz.enforcer import Action
from ring.fastapp.dependencies import (
    AuthenticatedRequestDependencies,
    get_request_dependencies,
    get_websocket_request_dependencies,
)
from ring.notebook.crud.document import (
    create_document,
    get_documents,
    update_document,
)
from ring.notebook.models.document import Document
from ring.notebook.schemas.document import (
    DocumentCreate,
    DocumentResponse,
    DocumentUpdate,
)
from ring.notebook.sync import notebook_websocket_server
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
    """Create a new document in a group the user belongs to."""
    group = cast(
        Group,
        load_and_check(
            req_dep.db,
            req_dep.current_user,
            Action.READ,
            document.group_api_id,
        ),
    )
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
    """List documents for a group the user belongs to."""
    group = cast(
        Group,
        load_and_check(
            req_dep.db,
            req_dep.current_user,
            Action.READ,
            group_api_id,
        ),
    )
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
    """Get a document by its API identifier."""
    return cast(
        Document,
        load_and_check(
            req_dep.db,
            req_dep.current_user,
            Action.READ,
            document_api_id,
        ),
    )


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
    """Update a document's name and/or rendered-HTML content projection."""
    db_document = cast(
        Document,
        load_and_check(
            req_dep.db,
            req_dep.current_user,
            Action.READ,
            document_api_id,
        ),
    )

    updated_document = update_document(
        req_dep.db,
        db_document,
        name=document_update.name,
        content=document_update.content,
    )

    req_dep.db.commit()
    return updated_document


@websocket_router.websocket("/{document_api_id}")
async def nb_document_websocket(
    websocket: WebSocket,
    document_api_id: str,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_websocket_request_dependencies
    ),
) -> None:
    """Yjs sync + awareness WebSocket for a notebook document.

    Speaks the standard y-websocket wire protocol: document updates are
    merged into the room's shared Doc and persisted; awareness messages
    (cursor positions, user presence) are relayed to all room clients.
    """
    try:
        load_and_check(
            req_dep.db,
            req_dep.current_user,
            Action.READ,
            document_api_id,
        )
    except (PermissionError, IDNotFoundException):
        # Reject before accepting the connection: handshake gets HTTP 403.
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    await notebook_websocket_server.serve(
        HttpxWebsocket(websocket, document_api_id)
    )
