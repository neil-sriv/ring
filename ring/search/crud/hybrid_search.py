from __future__ import annotations

from sqlalchemy.orm import Session

from ring.fastapp.fast import embedding_model
from ring.search.models.hybrid_search import HybridSearchDocument


def create_hybrid_search_document(
    db: Session, raw_text: str
) -> HybridSearchDocument:
    text_embedding = embedding_model.encode(raw_text).tolist()
    db_hybrid_search_document = HybridSearchDocument.create(
        raw_text=raw_text,
        text_embedding_384=text_embedding,
    )
    db.add(db_hybrid_search_document)
    return db_hybrid_search_document
