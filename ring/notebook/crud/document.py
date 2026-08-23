from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import select

from ring.notebook.models.document import Document
from ring.parties.models.group_model import Group
from ring.parties.models.user_model import User

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def create_document(
    db: Session,
    name: str,
    content: str,
    author: User,
    group: Group,
) -> Document:
    """Create a new document.

    Args:
        db (Session): Database session
        name (str): Name of the document
        content (str): Initial content of the document
        author (User): User creating the document
        group (Group): Group the document belongs to

    Returns:
        Document: Newly created document
    """
    db_document = Document.create(name=name, content=content, group=group)
    db.add(db_document)
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


def get_documents(
    db: Session,
    group: Group,
) -> list[Document]:
    """Get documents for a group."""
    return list(
        db.scalars(select(Document).where(Document.group_id == group.id)).all()
    )
