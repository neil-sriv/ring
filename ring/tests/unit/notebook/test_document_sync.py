"""Tests for the notebook Yjs sync layer.

Covers DocumentYStore persistence (write/read/apply, legacy-row tolerance)
and the document sync WebSocket endpoint (authz gating + sync handshake).
"""

from __future__ import annotations

import asyncio
from typing import Callable, Generator

import pytest
import sqlalchemy
from fastapi.testclient import TestClient
from pycrdt import Doc, Text, YMessageType, YSyncMessageType
from sqlalchemy.orm import Session
from starlette.websockets import WebSocketDisconnect

from ring.fastapp.dependencies import (
    AuthenticatedRequestDependencies,
    get_websocket_request_dependencies,
)
from ring.notebook.models.document import DocumentEdit
from ring.notebook.sync import DocumentYStore
from ring.parties.models.user_model import User
from ring.tests.factories.notebook.document_factory import (
    DocumentEditFactory,
    DocumentFactory,
)
from ring.tests.factories.parties.group_factory import GroupFactory


def _text_update(content: str) -> bytes:
    doc = Doc()
    text = doc.get("content", type=Text)
    text += content
    return doc.get_update()


def _read_text(store: DocumentYStore) -> str:
    doc = Doc()
    asyncio.run(store.apply_updates(doc))
    return str(doc.get("content", type=Text))


@pytest.fixture
def session_factory(db_session: Session) -> Callable[[], Session]:
    """Sessions joined to the test transaction, for DocumentYStore."""

    def _factory() -> Session:
        return Session(bind=db_session.get_bind())

    return _factory


class TestDocumentYStore:
    def test_write_and_apply_roundtrip(
        self,
        db_session: Session,
        session_factory: Callable[[], Session],
    ) -> None:
        document = DocumentFactory.create()
        db_session.commit()

        store = DocumentYStore(
            path=document.api_identifier, session_factory=session_factory
        )
        asyncio.run(store.write(_text_update("hello crdt")))

        edits = db_session.scalars(
            sqlalchemy.select(DocumentEdit).where(
                DocumentEdit.document_id == document.id
            )
        ).all()
        assert len(edits) == 1
        assert edits[0].author is None

        assert _read_text(store) == "hello crdt"

    def test_updates_accumulate_in_version_order(
        self,
        db_session: Session,
        session_factory: Callable[[], Session],
    ) -> None:
        document = DocumentFactory.create()
        db_session.commit()

        store = DocumentYStore(
            path=document.api_identifier, session_factory=session_factory
        )

        # Two sequential updates from the same source doc: the second is an
        # incremental continuation of the first.
        source = Doc()
        text = source.get("content", type=Text)
        text += "one"
        first = source.get_update()
        state = source.get_state()
        text += " two"
        second = source.get_update(state)

        asyncio.run(store.write(first))
        asyncio.run(store.write(second))

        assert _read_text(store) == "one two"

    def test_apply_updates_skips_legacy_html_rows(
        self,
        db_session: Session,
        session_factory: Callable[[], Session],
    ) -> None:
        """Pre-CRDT documents have an HTML initial edit; it must be ignored."""
        document = DocumentFactory.create()
        DocumentEditFactory.create(
            document=document, delta=b"<p>legacy html content</p>"
        )
        db_session.commit()

        store = DocumentYStore(
            path=document.api_identifier, session_factory=session_factory
        )
        asyncio.run(store.write(_text_update("fresh crdt state")))

        assert _read_text(store) == "fresh crdt state"


@pytest.fixture
def ws_client_for_user(
    unauthenticated_client: TestClient,
    db_session: Session,
    session_factory: Callable[[], Session],
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[Callable[[User], TestClient], None, None]:
    """Authenticate the WebSocket dependency as a given user.

    Also points the sync layer's session factory at the test transaction so
    room loads/persists see fixture data.
    """
    monkeypatch.setattr(
        "ring.notebook.sync.SessionLocal", lambda: session_factory()
    )

    def _method(user: User) -> TestClient:
        unauthenticated_client.app.dependency_overrides[
            get_websocket_request_dependencies
        ] = lambda: AuthenticatedRequestDependencies(
            db=db_session, current_user=user
        )
        return unauthenticated_client

    yield _method
    unauthenticated_client.app.dependency_overrides.pop(
        get_websocket_request_dependencies
    )


class TestDocumentSyncWebsocket:
    def test_member_gets_sync_step1(
        self,
        ws_client_for_user: Callable[[User], TestClient],
        db_session: Session,
    ) -> None:
        group = GroupFactory.create()
        member = group.admin
        document = DocumentFactory.create(group=group)
        db_session.commit()

        client = ws_client_for_user(member)
        with client.websocket_connect(
            f"/api/v1/ws/notebook/{document.api_identifier}"
        ) as websocket:
            message = websocket.receive_bytes()
        assert message[0] == YMessageType.SYNC
        assert message[1] == YSyncMessageType.SYNC_STEP1

    def test_non_member_is_rejected(
        self,
        ws_client_for_user: Callable[[User], TestClient],
        db_session: Session,
    ) -> None:
        document = DocumentFactory.create()
        outsider_group = GroupFactory.create()
        outsider = outsider_group.admin
        db_session.commit()

        client = ws_client_for_user(outsider)
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(
                f"/api/v1/ws/notebook/{document.api_identifier}"
            ) as websocket:
                websocket.receive_bytes()

    def test_unknown_document_is_rejected(
        self,
        ws_client_for_user: Callable[[User], TestClient],
        db_session: Session,
    ) -> None:
        group = GroupFactory.create()
        db_session.commit()

        client = ws_client_for_user(group.admin)
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(
                "/api/v1/ws/notebook/dcmnt_does-not-exist"
            ) as websocket:
                websocket.receive_bytes()
