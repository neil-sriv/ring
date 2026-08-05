from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Callable

from llm_service import (
    ApiClient,
    EmbeddingRequest,
    EmbeddingsApi,
)
from loguru import logger
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Query, Session

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
from ring.search.schemas.search import SearchSort, SearchType

SearchHit = tuple[SearchableType, str]


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
    entity_created_at: datetime,
    group_api_id: str | None = None,
    participant_api_id: str | None = None,
) -> HybridSearchDocument:
    # Embedding/semantic search is deprecated. Documents are indexed for
    # keyword search only (via the computed `text_tsv` column derived from
    # `raw_text`), so we no longer call the embedding service on write.
    db_hybrid_search_document = HybridSearchDocument.create(
        raw_text=raw_text,
    )
    association = HybridSearchDocumentAssociation.create(
        model_api_identifier=model_api_identifier,
        model_type=model_type.value,
        hybrid_search_document=db_hybrid_search_document,
        entity_created_at=entity_created_at,
        group_api_id=group_api_id,
        participant_api_id=participant_api_id,
    )
    db.add_all([db_hybrid_search_document, association])
    return db_hybrid_search_document


def _apply_search_filters(
    query: Query,
    group_api_id: str | None,
    participant_api_id: str | None,
) -> Query:
    if participant_api_id:
        query = query.filter(
            HybridSearchDocumentAssociation.model_type
            == SearchableType.RESPONSE.value,
            HybridSearchDocumentAssociation.participant_api_id
            == participant_api_id,
        )
    if group_api_id:
        query = query.filter(
            or_(
                HybridSearchDocumentAssociation.group_api_id == group_api_id,
                and_(
                    HybridSearchDocumentAssociation.model_type
                    == SearchableType.GROUP.value,
                    HybridSearchDocumentAssociation.model_api_identifier
                    == group_api_id,
                ),
            )
        )
    return query


def _apply_search_sort(
    query: Query,
    sort: SearchSort,
    ts_rank: object,
) -> Query:
    if sort == SearchSort.CREATED_AT_DESC:
        return query.order_by(
            HybridSearchDocumentAssociation.entity_created_at.desc(),
            ts_rank.desc(),
        )
    if sort == SearchSort.CREATED_AT_ASC:
        return query.order_by(
            HybridSearchDocumentAssociation.entity_created_at.asc(),
            ts_rank.desc(),
        )
    return query.order_by(ts_rank.desc())


def _document_search_base_query(db: Session) -> Query:
    return db.query(HybridSearchDocument).join(
        HybridSearchDocumentAssociation,
        HybridSearchDocumentAssociation.hybrid_search_document_id
        == HybridSearchDocument.id,
    )


def _hits_from_rows(rows: list) -> list[SearchHit]:
    hits: list[SearchHit] = []
    for row in rows:
        association = row[1]
        hits.append(
            (
                SearchableType(association.model_type),
                association.model_api_identifier,
            )
        )
    return hits


def _documents_from_rows(rows: list) -> list[HybridSearchDocument]:
    documents: list[HybridSearchDocument] = []
    for row in rows:
        if isinstance(row, HybridSearchDocument):
            documents.append(row)
        else:
            documents.append(row[0])
    return documents


def keyword_search_hybrid_search_document(
    db: Session,
    query: str,
    limit: int = 10,
    group_api_id: str | None = None,
    participant_api_id: str | None = None,
    sort: SearchSort = SearchSort.RELEVANCE,
) -> list[HybridSearchDocument]:
    tsquery = func.plainto_tsquery("english", query)
    ts_rank = func.ts_rank(HybridSearchDocument.text_tsv_expr_literal, tsquery)
    search_query = _document_search_base_query(db).filter(
        HybridSearchDocument.text_tsv_expr_literal.op("@@")(tsquery)
    )
    search_query = _apply_search_filters(
        search_query, group_api_id, participant_api_id
    )
    search_query = _apply_search_sort(search_query, sort, ts_rank)
    rows = search_query.limit(limit).all()
    return _documents_from_rows(rows)


def keyword_search_hits(
    db: Session,
    query: str,
    limit: int = 10,
    group_api_id: str | None = None,
    participant_api_id: str | None = None,
    sort: SearchSort = SearchSort.RELEVANCE,
) -> list[SearchHit]:
    tsquery = func.plainto_tsquery("english", query)
    ts_rank = func.ts_rank(HybridSearchDocument.text_tsv_expr_literal, tsquery)
    search_query = (
        _document_search_base_query(db)
        .add_columns(HybridSearchDocumentAssociation)
        .filter(HybridSearchDocument.text_tsv_expr_literal.op("@@")(tsquery))
    )
    search_query = _apply_search_filters(
        search_query, group_api_id, participant_api_id
    )
    search_query = _apply_search_sort(search_query, sort, ts_rank)
    rows = search_query.limit(limit).all()
    return _hits_from_rows(rows)


def semantic_search_hybrid_search_document(
    db: Session,
    query: str,
    limit: int = 10,
    group_api_id: str | None = None,
    participant_api_id: str | None = None,
    sort: SearchSort = SearchSort.RELEVANCE,
) -> list[HybridSearchDocument]:
    text_embedding = _generate_text_embedding(query)
    distance = HybridSearchDocument.text_embedding_768.l2_distance(
        text_embedding
    )
    search_query = _document_search_base_query(db).filter(distance < 0.5)
    search_query = _apply_search_filters(
        search_query, group_api_id, participant_api_id
    )
    if sort == SearchSort.CREATED_AT_DESC:
        search_query = search_query.order_by(
            HybridSearchDocumentAssociation.entity_created_at.desc(),
            distance,
        )
    elif sort == SearchSort.CREATED_AT_ASC:
        search_query = search_query.order_by(
            HybridSearchDocumentAssociation.entity_created_at.asc(),
            distance,
        )
    else:
        search_query = search_query.order_by(distance)
    rows = search_query.limit(limit).all()
    return _documents_from_rows(rows)


def semantic_search_hits(
    db: Session,
    query: str,
    limit: int = 10,
    group_api_id: str | None = None,
    participant_api_id: str | None = None,
    sort: SearchSort = SearchSort.RELEVANCE,
) -> list[SearchHit]:
    text_embedding = _generate_text_embedding(query)
    distance = HybridSearchDocument.text_embedding_768.l2_distance(
        text_embedding
    )
    search_query = (
        _document_search_base_query(db)
        .add_columns(HybridSearchDocumentAssociation)
        .filter(distance < 0.5)
    )
    search_query = _apply_search_filters(
        search_query, group_api_id, participant_api_id
    )
    if sort == SearchSort.CREATED_AT_DESC:
        search_query = search_query.order_by(
            HybridSearchDocumentAssociation.entity_created_at.desc(),
            distance,
        )
    elif sort == SearchSort.CREATED_AT_ASC:
        search_query = search_query.order_by(
            HybridSearchDocumentAssociation.entity_created_at.asc(),
            distance,
        )
    else:
        search_query = search_query.order_by(distance)
    rows = search_query.limit(limit).all()
    return _hits_from_rows(rows)


def dual_search_hybrid_search_document(
    db: Session,
    query: str,
    limit: int = 10,
    group_api_id: str | None = None,
    participant_api_id: str | None = None,
    sort: SearchSort = SearchSort.RELEVANCE,
) -> list[HybridSearchDocument]:
    text_embedding = _generate_text_embedding(query)
    tsquery = func.plainto_tsquery("english", query)
    distance = HybridSearchDocument.text_embedding_768.l2_distance(
        text_embedding
    )
    ts_rank = func.ts_rank(HybridSearchDocument.text_tsv_expr_literal, tsquery)
    search_query = _document_search_base_query(db).filter(
        or_(
            distance < 0.5,
            HybridSearchDocument.text_tsv_expr_literal.op("@@")(tsquery),
        )
    )
    search_query = _apply_search_filters(
        search_query, group_api_id, participant_api_id
    )
    if sort == SearchSort.CREATED_AT_DESC:
        search_query = search_query.order_by(
            HybridSearchDocumentAssociation.entity_created_at.desc(),
            distance,
            ts_rank.desc(),
        )
    elif sort == SearchSort.CREATED_AT_ASC:
        search_query = search_query.order_by(
            HybridSearchDocumentAssociation.entity_created_at.asc(),
            distance,
            ts_rank.desc(),
        )
    else:
        search_query = search_query.order_by(distance, ts_rank.desc())
    rows = search_query.limit(limit).all()
    return _documents_from_rows(rows)


def dual_search_hits(
    db: Session,
    query: str,
    limit: int = 10,
    group_api_id: str | None = None,
    participant_api_id: str | None = None,
    sort: SearchSort = SearchSort.RELEVANCE,
) -> list[SearchHit]:
    text_embedding = _generate_text_embedding(query)
    tsquery = func.plainto_tsquery("english", query)
    distance = HybridSearchDocument.text_embedding_768.l2_distance(
        text_embedding
    )
    ts_rank = func.ts_rank(HybridSearchDocument.text_tsv_expr_literal, tsquery)
    search_query = (
        _document_search_base_query(db)
        .add_columns(HybridSearchDocumentAssociation)
        .filter(
            or_(
                distance < 0.5,
                HybridSearchDocument.text_tsv_expr_literal.op("@@")(tsquery),
            )
        )
    )
    search_query = _apply_search_filters(
        search_query, group_api_id, participant_api_id
    )
    if sort == SearchSort.CREATED_AT_DESC:
        search_query = search_query.order_by(
            HybridSearchDocumentAssociation.entity_created_at.desc(),
            distance,
            ts_rank.desc(),
        )
    elif sort == SearchSort.CREATED_AT_ASC:
        search_query = search_query.order_by(
            HybridSearchDocumentAssociation.entity_created_at.asc(),
            distance,
            ts_rank.desc(),
        )
    else:
        search_query = search_query.order_by(distance, ts_rank.desc())
    rows = search_query.limit(limit).all()
    return _hits_from_rows(rows)


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


def hydrate_ordered_results(
    db: Session,
    ordered_hits: list[SearchHit],
) -> list[APIIdentified]:
    if not ordered_hits:
        return []

    ids_by_type: dict[SearchableType, set[str]] = defaultdict(set)
    for model_type, api_identifier in ordered_hits:
        ids_by_type[model_type].add(api_identifier)

    models_by_hit: dict[SearchHit, APIIdentified] = {}
    for model_type, api_identifiers in ids_by_type.items():
        for model in hydrate_results(db, model_type, list(api_identifiers)):
            models_by_hit[(model_type, model.api_identifier)] = model

    hydrated_results: list[APIIdentified] = []
    for hit in ordered_hits:
        if model := models_by_hit.get(hit):
            hydrated_results.append(model)
    return hydrated_results


def search(
    db: Session,
    query: str,
    user: User,
    limit: int = 10,
    search_type: SearchType = SearchType.KEYWORD,
    group_api_id: str | None = None,
    participant_api_id: str | None = None,
    sort: SearchSort = SearchSort.RELEVANCE,
) -> list[APIIdentified]:
    search_hit_dispatch: dict[
        SearchType,
        Callable[..., list[SearchHit]],
    ] = {
        SearchType.SEMANTIC: semantic_search_hits,
        SearchType.KEYWORD: keyword_search_hits,
        SearchType.DUAL: dual_search_hits,
    }
    fetch_limit = limit * 3
    ordered_hits = search_hit_dispatch[search_type](
        db,
        query,
        limit=fetch_limit,
        group_api_id=group_api_id,
        participant_api_id=participant_api_id,
        sort=sort,
    )
    hydrated_results = hydrate_ordered_results(db, ordered_hits)
    authorized_results = filter_to_authorized(
        db, user, Action.READ, hydrated_results
    )
    return authorized_results[:limit]
