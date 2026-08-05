from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ring.fastapp.dependencies import (
    AuthenticatedRequestDependencies,
    get_db,
    get_request_dependencies,
)
from ring.ring_pydantic.linked_schemas import SearchResponse, SearchResult
from ring.search.crud.hybrid_search import (
    dual_search_hybrid_search_document,
    keyword_search_hybrid_search_document,
    search,
    semantic_search_hybrid_search_document,
)
from ring.search.schemas.search import (
    RawSearchResponse,
    RawSearchResult,
    SearchSort,
    SearchType,
)

router = APIRouter()


@router.get("/raw-search", response_model=RawSearchResponse)
async def raw_search(
    query: str,
    search_type: SearchType = SearchType.KEYWORD,
    limit: int = 10,
    group_api_id: str | None = None,
    participant_api_id: str | None = None,
    sort: SearchSort = SearchSort.RELEVANCE,
    db: Session = Depends(get_db),
) -> RawSearchResponse:
    """
    Search the search table for a given query.

    Args:
        query: The search query string
        search_type: Type of search to perform (semantic, keyword, or dual)
        limit: Maximum number of results to return
        group_api_id: Optional group filter
        participant_api_id: Optional responder filter (responses only)
        sort: Result ordering
        db: Database session

    Returns:
        RawSearchResponse containing matching results and total count
    """
    if not query.strip():
        raise HTTPException(
            status_code=400, detail="Search query cannot be empty"
        )

    search_functions = {
        SearchType.SEMANTIC: semantic_search_hybrid_search_document,
        SearchType.KEYWORD: keyword_search_hybrid_search_document,
        SearchType.DUAL: dual_search_hybrid_search_document,
    }

    if search_type not in search_functions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid search type. Must be one of: {', '.join(search_functions.keys())}",
        )

    search_func = search_functions[search_type]
    results = search_func(
        db=db,
        query=query,
        limit=limit,
        group_api_id=group_api_id,
        participant_api_id=participant_api_id,
        sort=sort,
    )

    return RawSearchResponse(
        results=[RawSearchResult.model_validate(result) for result in results],
        total=len(results),
    )


@router.get("/search", response_model=SearchResponse)
async def perform_search(
    query: str,
    search_type: SearchType = SearchType.KEYWORD,
    limit: int = 10,
    group_api_id: str | None = None,
    participant_api_id: str | None = None,
    sort: SearchSort = SearchSort.RELEVANCE,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> SearchResponse:
    results = search(
        db=req_dep.db,
        query=query,
        user=req_dep.current_user,
        limit=limit,
        search_type=search_type,
        group_api_id=group_api_id,
        participant_api_id=participant_api_id,
        sort=sort,
    )
    return SearchResponse(
        results=[SearchResult.from_model(result) for result in results],
        total=len(results),
    )
