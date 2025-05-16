from __future__ import annotations

from sqlalchemy import func
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


def semantic_search_hybrid_search_document(
    db: Session, query: str, limit: int = 10
) -> list[HybridSearchDocument]:
    text_embedding = embedding_model.encode(query).tolist()
    return (
        db.query(HybridSearchDocument)
        .filter(
            HybridSearchDocument.text_embedding_384.l2_distance(text_embedding)
            < 0.5
        )
        .order_by(
            HybridSearchDocument.text_embedding_384.l2_distance(text_embedding)
        )
        .limit(limit)
        .all()
    )


def keyword_search_hybrid_search_document(
    db: Session, query: str, limit: int = 10
) -> list[HybridSearchDocument]:
    tsquery = func.plainto_tsquery("english", query)
    return (
        db.query(HybridSearchDocument)
        .filter(HybridSearchDocument.text_tsv_expr_literal.op("@@")(tsquery))
        .order_by(
            func.ts_rank(
                HybridSearchDocument.text_tsv_expr_literal, tsquery
            ).desc()
        )
        .limit(limit)
        .all()
    )
