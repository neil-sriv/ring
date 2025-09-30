from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import Callable

from llm_service import (
    ApiClient,
    EmbeddingRequest,
    EmbeddingsApi,
)
from loguru import logger
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ring.api_identifier.api_identified_model import APIIdentified
from ring.api_identifier.util import get_models
from ring.authz.authz import filter_to_authorized
from ring.authz.enforcer import Action
from ring.fastapp.config import get_llm_config
from ring.lib.util import RegistrationDict
from ring.parties.models.user_model import User
from ring.search.models.hybrid_search import (
    HybridSearchDocument,
    HybridSearchDocumentAssociation,
    SearchableType,
)
from ring.search.schemas.search import SearchType


@dataclass
class SearchRegistration:
    model_class: type[APIIdentified]
    search_function: Callable[[Session, APIIdentified], HybridSearchDocument]
    search_type: SearchableType


SEARCH_REGISTRY: RegistrationDict[SearchableType, SearchRegistration] = (
    RegistrationDict("SEARCH_REGISTRY")
)


def register_search_function(
    searchable_type: SearchableType,
    model_class: type[APIIdentified],
):
    def decorator(
        search_function: Callable[
            [Session, APIIdentified], HybridSearchDocument
        ],
    ):
        @wraps(search_function)
        def wrapper(*args, **kwargs):
            try:
                return search_function(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in search function: {e}")
                # raise e
                return None

        SEARCH_REGISTRY[searchable_type.value] = SearchRegistration(
            model_class=model_class,
            search_function=wrapper,
            search_type=searchable_type,
        )
        return wrapper

    return decorator


def type_to_search_registration(
    searchable_type: SearchableType,
) -> SearchRegistration:
    return SEARCH_REGISTRY[searchable_type]


def model_class_to_search_registration(
    model: type[APIIdentified],
) -> SearchRegistration:
    for registration in SEARCH_REGISTRY.values():
        if registration.model_class == model:
            return registration
    raise ValueError(f"Model {model} not found in SEARCH_REGISTRY")


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
        assocation_groups[SearchableType(assocation.model_type)].append(
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
        SEARCH_REGISTRY[model_type].model_class,
        model_api_identifiers,
        raise_on_missing=False,
    )


def search(
    db: Session,
    query: str,
    user: User,
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
    hydrated_results = filter_to_authorized(
        db, user, Action.READ, hydrated_results
    )
    return hydrated_results
