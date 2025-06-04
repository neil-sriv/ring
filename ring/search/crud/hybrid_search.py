from __future__ import annotations

from collections import defaultdict
from enum import Enum
from functools import wraps

from llm_service import (
    ApiClient,
    EmbeddingRequest,
    EmbeddingsApi,
)
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ring.api_identifier.api_identified_model import APIIdentified
from ring.api_identifier.util import get_models
from ring.fastapp.config import get_llm_config
from ring.lib.util import RegistrationDict
from ring.search.models.hybrid_search import (
    HybridSearchDocument,
    HybridSearchDocumentAssociation,
)
from ring.search.schemas.search import SearchType

SEARCH_MODEL_REGISTRY: RegistrationDict[
    SearchableType, type[APIIdentified]
] = RegistrationDict("SEARCH_MODEL_REGISTRY")


class SearchableType(str, Enum):
    USER = "user"
    GROUP = "group"
    RESPONSE = "response"
    LETTER = "letter"
    QUESTION = "question"


def register_searchable_model(model_type: SearchableType):
    """Decorator to register a model as searchable.

    :param model_type: Type identifier for the model
    """

    def decorator(cls: type[APIIdentified]) -> type[APIIdentified]:
        @wraps(cls)
        def wrapper(*args, **kwargs):
            return cls(*args, **kwargs)

        SEARCH_MODEL_REGISTRY[model_type.value] = cls
        return cls

    return decorator


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
    db: Session,
    raw_text: str,
    model_api_identifier: str,
    model_type: SearchableType,
) -> HybridSearchDocument:
    text_embedding = _generate_text_embedding(raw_text)
    db_hybrid_search_document = HybridSearchDocument.create(
        raw_text=raw_text,
        text_embedding_768=text_embedding,
    )
    association = HybridSearchDocumentAssociation.create(
        model_api_identifier=model_api_identifier,
        model_type=model_type.value,
        hybrid_search_document=db_hybrid_search_document,
    )
    db.add_all([db_hybrid_search_document, association])
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


def get_model_ids_from_hybrid_search_documents(
    db: Session, hybrid_search_documents: list[HybridSearchDocument]
) -> dict[str, list[str]]:
    assocation_groups: dict[str, list[str]] = defaultdict(list)
    assocations = db.scalars(
        select(HybridSearchDocumentAssociation).filter(
            HybridSearchDocumentAssociation.hybrid_search_document_id.in_(
                [document.id for document in hybrid_search_documents]
            )
        )
    )
    for assocation in assocations:
        assocation_groups[assocation.model_type].append(
            assocation.model_api_identifier
        )
    return assocation_groups


def hydrate_results(
    db: Session,
    model_type: SearchableType,
    model_api_identifiers: list[str],
) -> list[APIIdentified]:
    return get_models(
        db,
        SEARCH_MODEL_REGISTRY[model_type.value],
        model_api_identifiers,
    )


def search(
    db: Session,
    query: str,
    limit: int = 10,
    search_type: SearchType = SearchType.DUAL,
) -> list[APIIdentified]:
    search_results = dual_search_hybrid_search_document(db, query, limit)
    model_ids_by_type = get_model_ids_from_hybrid_search_documents(
        db, search_results
    )
    hydrated_results = []
    for model_type, model_api_identifiers in model_ids_by_type.items():
        hydrated_results.extend(
            hydrate_results(db, model_type, model_api_identifiers)
        )
    return hydrated_results
