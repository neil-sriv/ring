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
from sqlalchemy.orm import Session, load_only, selectinload

from ring.api_identifier.api_identified_model import APIIdentified
from ring.authz.authz import filter_to_authorized
from ring.authz.enforcer import Action
from ring.fastapp.config import get_llm_config
from ring.letters.models.letter_model import Letter
from ring.letters.models.question_model import Question
from ring.letters.models.response_model import Response
from ring.lib.util import RegistrationDict
from ring.parties.models.group_model import Group
from ring.parties.models.user_model import User
from ring.search.models.hybrid_search import (
    HybridSearchDocument,
    HybridSearchDocumentAssociation,
    SearchableType,
)
from ring.search.schemas.search import SearchType


SearchModelReference = tuple[SearchableType, str]
SEARCH_AUTHZ_OVERFETCH_MULTIPLIER = 3
SEARCH_AUTHZ_OVERFETCH_CAP = 100


@dataclass
class SearchRegistration:
    model_class: type[APIIdentified]
    # Wrappers catch indexing failures and return None so entity creates are
    # not blocked by search errors; callers (e.g. backfill) must handle None.
    search_function: Callable[
        [Session, APIIdentified], HybridSearchDocument | None
    ]
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
    ) -> Callable[[Session, APIIdentified], HybridSearchDocument | None]:
        @wraps(search_function)
        def wrapper(
            db: Session, model: APIIdentified
        ) -> HybridSearchDocument | None:
            try:
                return search_function(db, model)
            except Exception as e:
                logger.error(f"Error in search function: {e}")
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
        .options(
            load_only(HybridSearchDocument.id, HybridSearchDocument.raw_text)
        )
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
) -> list[SearchModelReference]:
    if not hybrid_search_documents:
        return []

    document_rank = {
        document.id: index
        for index, document in enumerate(hybrid_search_documents)
    }
    associations = db.execute(
        select(
            HybridSearchDocumentAssociation.hybrid_search_document_id,
            HybridSearchDocumentAssociation.model_api_identifier,
            HybridSearchDocumentAssociation.model_type,
        ).filter(
            HybridSearchDocumentAssociation.hybrid_search_document_id.in_(
                list(document_rank)
            )
        )
    ).all()

    ordered_model_ids: list[SearchModelReference] = []
    seen_model_ids: set[SearchModelReference] = set()
    for _document_id, model_api_identifier, model_type in sorted(
        associations,
        key=lambda association: document_rank[association[0]],
    ):
        model_reference = (
            SearchableType(model_type),
            model_api_identifier,
        )
        if model_reference in seen_model_ids:
            continue
        ordered_model_ids.append(model_reference)
        seen_model_ids.add(model_reference)
    return ordered_model_ids


def hydrate_results(
    db: Session,
    model_type: SearchableType,
    model_api_identifiers: list[str],
) -> list[APIIdentified]:
    if not model_api_identifiers:
        return []

    model_class = SEARCH_REGISTRY[model_type].model_class
    models = (
        db.query(model_class)
        .options(*_search_result_load_options(model_type))
        .filter(model_class.api_identifier.in_(model_api_identifiers))
        .all()
    )
    models_by_api_identifier = {
        model.api_identifier: model for model in models
    }
    return [
        models_by_api_identifier[api_identifier]
        for api_identifier in model_api_identifiers
        if api_identifier in models_by_api_identifier
    ]


def search(
    db: Session,
    query: str,
    user: User,
    limit: int = 10,
    search_type: SearchType = SearchType.KEYWORD,
) -> list[APIIdentified]:
    # Resolve the search function at call time (rather than via a module-level
    # dict) so the names stay patchable in tests.
    search_dispatch: dict[
        SearchType,
        Callable[[Session, str, int], list[HybridSearchDocument]],
    ] = {
        SearchType.SEMANTIC: semantic_search_hybrid_search_document,
        SearchType.KEYWORD: keyword_search_hybrid_search_document,
        SearchType.DUAL: dual_search_hybrid_search_document,
    }
    if limit <= 0:
        return []

    search_results = search_dispatch[search_type](
        db, query, _search_overfetch_limit(limit)
    )
    model_references = get_model_ids_from_hybrid_search_documents(
        db, search_results
    )
    model_ids_by_type: dict[SearchableType, list[str]] = defaultdict(list)
    for model_type, model_api_identifier in model_references:
        model_ids_by_type[model_type].append(model_api_identifier)

    hydrated_results_by_api_identifier: dict[str, APIIdentified] = {}
    for model_type, model_api_identifiers in model_ids_by_type.items():
        for result in hydrate_results(db, model_type, model_api_identifiers):
            hydrated_results_by_api_identifier[result.api_identifier] = result

    ranked_results = [
        hydrated_results_by_api_identifier[model_api_identifier]
        for _, model_api_identifier in model_references
        if model_api_identifier in hydrated_results_by_api_identifier
    ]
    authorized_results = filter_to_authorized(
        db, user, Action.READ, ranked_results
    )
    return list(authorized_results)[:limit]


def _search_overfetch_limit(limit: int) -> int:
    return min(
        limit * SEARCH_AUTHZ_OVERFETCH_MULTIPLIER,
        SEARCH_AUTHZ_OVERFETCH_CAP,
    )


def _search_result_load_options(model_type: SearchableType) -> list:
    if model_type == SearchableType.USER:
        return [selectinload(User.groups)]

    if model_type == SearchableType.GROUP:
        return [
            selectinload(Group.members),
            selectinload(Group.letters),
        ]

    if model_type == SearchableType.LETTER:
        return [
            selectinload(Letter.group),
            selectinload(Letter.participants),
            selectinload(Letter.questions),
        ]

    if model_type == SearchableType.QUESTION:
        return [
            selectinload(Question.letter).selectinload(Letter.group),
            selectinload(Question.responses),
        ]

    if model_type == SearchableType.RESPONSE:
        return [
            selectinload(Response.participant),
            selectinload(Response.question)
            .selectinload(Question.letter)
            .selectinload(Letter.group),
        ]

    return []
