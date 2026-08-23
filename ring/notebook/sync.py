"""Yjs CRDT synchronization for notebook documents.

Serves the standard Yjs sync + awareness WebSocket protocol (the one spoken by
``y-websocket`` / TipTap's Collaboration extensions) using pycrdt, and persists
document updates into the ``document_edits`` table.

Rooms are process-local, matching the single-process uvicorn deployment.
"""

from __future__ import annotations

from logging import Logger, getLogger
from typing import AsyncIterator, Awaitable, Callable

from anyio import CancelScope, to_thread
from pycrdt import Doc
from pycrdt.store import BaseYStore
from pycrdt.websocket import WebsocketServer, YRoom
from pycrdt.websocket.websocket_server import exception_logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from ring.api_identifier.util import get_model
from ring.notebook.models.document import Document, DocumentEdit
from ring.sqlalchemy_base import SessionLocal

SessionFactory = Callable[[], Session]


def _session_factory(override: SessionFactory | None) -> SessionFactory:
    # Resolve lazily so tests can patch ring.notebook.sync.SessionLocal.
    return override if override is not None else SessionLocal


class DocumentYStore(BaseYStore):
    """Persist Yjs updates for one document as ``document_edits`` rows.

    ``path`` is the document ``api_identifier``. Every incremental Yjs update
    broadcast by the room is appended as one row; loading a room replays all
    rows in version order.
    """

    def __init__(
        self,
        path: str,
        metadata_callback: Callable[[], Awaitable[bytes] | bytes]
        | None = None,
        log: Logger | None = None,
        session_factory: SessionFactory | None = None,
    ):
        self.path = path
        self.metadata_callback = metadata_callback
        self.log = log or getLogger(__name__)
        self._session_override = session_factory

    async def write(self, data: bytes) -> None:
        # Shielded: room teardown must not drop the final typed characters.
        with CancelScope(shield=True):
            await to_thread.run_sync(self._write_sync, data)

    def _write_sync(self, data: bytes) -> None:
        with _session_factory(self._session_override)() as db:
            document = get_model(db, Document, self.path)
            db.add(DocumentEdit(document=document, delta=data))
            db.commit()

    async def read(self) -> AsyncIterator[tuple[bytes, bytes, float]]:
        edits = await to_thread.run_sync(self._read_sync)
        for delta, timestamp in edits:
            yield delta, b"", timestamp

    def _read_sync(self) -> list[tuple[bytes, float]]:
        with _session_factory(self._session_override)() as db:
            document = get_model(db, Document, self.path)
            edits = db.scalars(
                select(DocumentEdit)
                .where(DocumentEdit.document_id == document.id)
                .order_by(DocumentEdit.version)
            ).all()
            return [
                (edit.delta, edit.created_at.timestamp()) for edit in edits
            ]

    async def apply_updates(self, ydoc: Doc) -> None:
        """Apply stored updates, skipping rows that are not Yjs updates.

        Documents created before the CRDT rewrite have an initial
        ``document_edits`` row containing raw HTML; those are not part of the
        CRDT history and are ignored.
        """
        async for update, *_ in self.read():
            try:
                ydoc.apply_update(update)
            except Exception:
                self.log.warning(
                    "Skipping non-Yjs document_edits row for %s", self.path
                )


class NotebookWebsocketServer(WebsocketServer):
    """WebsocketServer that loads and persists rooms through DocumentYStore."""

    def __init__(self, session_factory: SessionFactory | None = None):
        super().__init__(exception_handler=exception_logger)
        self._session_override = session_factory

    async def get_room(self, name: str) -> YRoom:
        if name not in self.rooms:
            ystore = DocumentYStore(
                path=name,
                log=self.log,
                session_factory=self._session_override,
            )
            room = YRoom(
                ready=False,
                ystore=ystore,
                exception_handler=self.exception_handler,
                log=self.log,
            )
            self.rooms[name] = room
            await self.start_room(room)
            try:
                await ystore.apply_updates(room.ydoc)
            finally:
                # Mark ready even on load failure so waiters don't hang;
                # the exception handler has already logged the problem.
                room.ready = True
            return room

        room = self.rooms[name]
        await self.start_room(room)
        if not room.ready:
            # Another connection is still replaying history; wait so this
            # client's initial sync includes it.
            await room.ready_event.wait()
        return room


notebook_websocket_server = NotebookWebsocketServer()
