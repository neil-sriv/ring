from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ring.fastapp.dependencies import get_db
from ring.search.crud.hybrid_search import (
    dual_search_hybrid_search_document,
    keyword_search_hybrid_search_document,
    semantic_search_hybrid_search_document,
)
from ring.search.schemas.search import SearchResponse, SearchResult

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/letters", response_model=SearchResponse)
async def search_letters(
    query: str,
    search_type: str = "dual",  # Options: "semantic", "keyword", "dual"
    limit: int = 10,
    db: Session = Depends(get_db),
) -> SearchResponse:
    """
    Search through letter content using various search methods.

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
        "semantic": semantic_search_hybrid_search_document,
        "keyword": keyword_search_hybrid_search_document,
        "dual": dual_search_hybrid_search_document,
    }

    if search_type not in search_functions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid search type. Must be one of: {', '.join(search_functions.keys())}",
        )

    search_func = search_functions[search_type]
    results = search_func(db=db, query=query, limit=limit)

    return SearchResponse(
        results=[SearchResult.model_validate(result) for result in results],
        total=len(results),
    )
