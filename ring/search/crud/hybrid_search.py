from __future__ import annotations

from llm_service import (
    ApiClient,
    EmbeddingRequest,
    EmbeddingsApi,
)
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ring.fastapp.config import get_llm_config
from ring.search.models.hybrid_search import HybridSearchDocument


def _generate_text_embedding(text: str) -> list[float | int]:
    """
    Generate a text embedding using LLM service.

    :param text: Text to generate the embedding for
    :return: Text embedding
    """
    api_client = ApiClient(configuration=get_llm_config().config)
    api_instance = EmbeddingsApi(api_client=api_client)
    embedding_request = EmbeddingRequest(text=text)
    embedding_response = api_instance.embed_embeddings_embed_post(
        embedding_request
    )
    return embedding_response.embedding


def create_hybrid_search_document(
    db: Session, raw_text: str
) -> HybridSearchDocument:
    text_embedding = _generate_text_embedding(raw_text)
    db_hybrid_search_document = HybridSearchDocument.create(
        raw_text=raw_text,
        text_embedding_768=text_embedding,
    )
    db.add(db_hybrid_search_document)
    return db_hybrid_search_document


def semantic_search_hybrid_search_document(
    db: Session, query: str, limit: int = 10
) -> list[HybridSearchDocument]:
    text_embedding = _generate_text_embedding(query)
    return (
        db.query(HybridSearchDocument)
        .filter(
            HybridSearchDocument.text_embedding_768.l2_distance(text_embedding)
            < 0.5
        )
        .order_by(
            HybridSearchDocument.text_embedding_768.l2_distance(text_embedding)
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


def dual_search_hybrid_search_document(
    db: Session, query: str, limit: int = 10
) -> list[HybridSearchDocument]:
    text_embedding = _generate_text_embedding(query)
    tsquery = func.plainto_tsquery("english", query)
    return (
        db.query(HybridSearchDocument)
        .filter(
            or_(
                HybridSearchDocument.text_embedding_768.l2_distance(
                    text_embedding
                )
                < 0.5,
                HybridSearchDocument.text_tsv_expr_literal.op("@@")(tsquery),
            )
        )
        .order_by(
            HybridSearchDocument.text_embedding_768.l2_distance(
                text_embedding
            ),
            func.ts_rank(
                HybridSearchDocument.text_tsv_expr_literal, tsquery
            ).desc(),
        )
        .limit(limit)
        .all()
    )
