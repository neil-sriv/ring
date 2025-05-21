from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ring.fastapp.dependencies import get_db
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
    SearchType,
)

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/raw-search", response_model=RawSearchResponse)
async def raw_search(
    query: str,
    search_type: SearchType = SearchType.DUAL,
    limit: int = 10,
    db: Session = Depends(get_db),
) -> RawSearchResponse:
    """
    Search the search table for a given query.

    Args:
        query: The search query string
        search_type: Type of search to perform (semantic, keyword, or dual)
        limit: Maximum number of results to return
        db: Database session

    Returns:
        SearchResponse containing matching results and total count
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
    results = search_func(db=db, query=query, limit=limit)

    return RawSearchResponse(
        results=[RawSearchResult.model_validate(result) for result in results],
        total=len(results),
    )


@router.get("/search", response_model=SearchResponse)
async def perform_search(
    query: str,
    search_type: SearchType = SearchType.DUAL,
    limit: int = 10,
    db: Session = Depends(get_db),
) -> SearchResponse:
    results = search(db=db, query=query, limit=limit)
    return SearchResponse(
        results=[SearchResult.from_model(result) for result in results],
        total=len(results),
    )
