from __future__ import annotations

from loguru import logger
from sqlalchemy.orm import Session

from ring.api_identifier.util import get_model
from ring.notebook.models.document import Document, DocumentEdit
from ring.parties.models.user_model import User


class SQLAlchemyStore:
    def __init__(self, db: Session, document_api_id: str, user: User):
        self.db: Session = db
        self.document_api_id: str = document_api_id
        self.user: User = user
        self._document: Document | None = None

    def get_document(self) -> Document | None:
        if self._document is None:
            try:
                self._document = get_model(
                    self.db, Document, self.document_api_id
                )
            except Exception:
                self._document = None
        return self._document

    def create_document(self, name: str, content: bytes) -> Document:
        document = Document(
            name=name, content=content, latest_snapshot_version=0
        )
        self.db.add(document)
        self.db.commit()
        self._document = document
        return document

    def save_update(self, update: bytes, doc: Doc) -> DocumentEdit:
        document = self.get_document()
        if not document:
            document = self.create_document("Untitled Document", b"")

        document_edit = DocumentEdit(
            document=document,
            delta=update,
            author=self.user,
        )

        self.db.add(document_edit)
        self.db.flush()
        self.db.refresh(document_edit)
        document.latest_snapshot_version = document_edit.version
        self.db.commit()
        return document_edit

    def load_document_state(self) -> bytes:
        document = self.get_document()
        if not document:
            return b""

        edits = sorted(document.edits, key=lambda edit: edit.version)
        if not edits:
            return b""

        from pycrdt import merge_updates

        updates = [edit.delta for edit in edits]
        return merge_updates(*updates)

    def get_updates_since(self, version: int) -> list[bytes]:
        document = self.get_document()
        if not document:
            return []
        return [
            edit.delta for edit in document.edits if edit.version > version
        ]
