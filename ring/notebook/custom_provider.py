from __future__ import annotations

from loguru import logger
from pycrdt import Channel, Doc, Provider

from ring.notebook.sqlalchemy_store import SQLAlchemyStore


class CustomProvider(Provider):
    store: SQLAlchemyStore
    _initialized: bool

    def __init__(
        self, doc: Doc, channel: Channel, store: SQLAlchemyStore, log=None
    ):
        super().__init__(doc, channel, log)
        self.store = store
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
        self._initialized = True

        document = self.store.get_document()
        if document is None:
            self.store.create_document("Untitled Document", b"")
        else:
            existing_content = self.store.load_document_state()
            if existing_content and len(existing_content) > 0:
                self._doc.apply_update(existing_content)

        self._initialized = True

    async def _send_updates(self):
        try:
            async with self._doc.events() as events:
                async for event in events:
                    self.store.save_update(event.update, self._doc)
                    try:
                        from pycrdt import create_update_message

                        message = create_update_message(event.update)
                        await self._channel.send(message)
                    except Exception:
                        pass
        except Exception as e:
            logger.error(f"Error in _send_updates: {e}")
