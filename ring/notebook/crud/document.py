from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from fastapi import WebSocket
from loguru import logger
from sqlalchemy import Sequence, select

from ring.api_identifier.util import bulk_get_models
from ring.notebook.models.document import Document, DocumentEdit
from ring.parties.models.user_model import User

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

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
        if connection == sender:
            continue
        try:
            await connection.send_bytes(data)
        except Exception as e:
            logger.error(f"Failed to send message to connection: {e}")
            # Remove dead connections
            room.active_connections.remove(connection)


# Document CRUD operations
def create_document(
    db: Session,
    name: str,
    content: str,
    author: User,
) -> Document:
    """Create a new document.

    Args:
        db (Session): Database session
        name (str): Name of the document
        content (str): Initial content of the document
        author (User): User creating the document

    Returns:
        Document: Newly created document
    """
    db_document = Document.create(name=name, content=content)
    db.add(db_document)

    # Create initial edit
    initial_edit = DocumentEdit(
        document=db_document,
        delta=content.encode("utf-8"),
        author=author,
    )
    db.add(initial_edit)

    return db_document


def update_document(
    db: Session,
    document: Document,
    name: Optional[str] = None,
    content: Optional[str] = None,
) -> Document:
    """Update a document.

    Args:
        db (Session): Database session
        document (Document): Document to update
        name (Optional[str], optional): New name for the document. Defaults to None.
        content (Optional[str], optional): New content for the document. Defaults to None.

    Returns:
        Document: Updated document
    """
    if name is not None:
        document.name = name
    if content is not None:
        document.content = content.encode("utf-8")

    db.add(document)
    return document


# def get_documents(
#     db: Session,
#     group_api_id: str,
# ) -> Sequence[Document]:
#     """Get documents for a group."""
#     document_ids = db.scalars(
#         select(Document.id).where(Document.group_api_id == group_api_id)
#     )
#     return bulk_get_models(db, Document, document_ids)


def snapshot_document(
    db: Session,
    document: Document,
    document_edit: DocumentEdit,
) -> Document:
    """Snapshot a document."""
    document.content = document_edit.delta
    document.latest_snapshot_version = document_edit.version
    return document


def add_document_edit(
    db: Session,
    document: Document,
    delta: bytes,
    author: User,
) -> DocumentEdit:
    """Add an edit to a document.

    Args:
        db (Session): Database session
        document (Document): Document to edit
        delta (str): Delta/change to apply
        author (User): User making the edit

    Returns:
        DocumentEdit: Newly created edit
    """

    edit = DocumentEdit(
        delta=delta,
        document=document,
        author=author,
    )

    db.add(edit)

    return edit
