from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from ring.fastapp.dependencies import (
    AuthenticatedRequestDependencies,
    get_request_dependencies,
)
from ring.search.crud.hybrid_search import (
    dual_search_hybrid_search_document,
    keyword_search_hybrid_search_document,
    search,
    semantic_search_hybrid_search_document,
)
from ring.search.models.hybrid_search import SearchableType
from ring.search.schemas.search import (
    RawSearchResponse,
    RawSearchResult,
    SearchHit,
    SearchResponse,
    SearchType,
)

router = APIRouter()


@router.get("/raw-search", response_model=RawSearchResponse)
async def raw_search(
    query: str,
    search_type: SearchType = SearchType.KEYWORD,
    limit: int = 10,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> RawSearchResponse:
    """
    Search the search table for a given query.

    Args:
        query: The search query string
        search_type: Type of search to perform (semantic, keyword, or dual)
        limit: Maximum number of results to return
        req_dep: Authenticated request dependencies

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
    results = search_func(db=req_dep.db, query=query, limit=limit)

    return RawSearchResponse(
        results=[RawSearchResult.model_validate(result) for result in results],
        total=len(results),
    )


@router.get("/search", response_model=SearchResponse)
async def perform_search(
    query: str,
    search_type: SearchType = SearchType.KEYWORD,
    limit: int = 10,
    offset: int = 0,
    types: Annotated[list[SearchableType] | None, Query()] = None,
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> SearchResponse:
    """Search groups, letters, questions, and responses.

    The query supports GitHub-style qualifiers in addition to free text:
    - `author:name` or `author:"Full Name"` — questions by that author and
      responses by that participant (name or email, case-insensitive)
    - `status:open` — currently in-progress issues
    - `status:published` — sent issues
    - `status:upcoming` — scheduled issues
    - `is:open` / `is:published` — aliases of `status:`
    - `author:@me` — the current user
    """
    results = search(
        db=req_dep.db,
        query=query,
        user=req_dep.current_user,
        limit=limit,
        offset=offset,
        search_type=search_type,
        model_types=types,
    )
    return SearchResponse(
        results=[SearchHit.from_model(result) for result in results],
        total=len(results),
    )
