from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from ring.fastapp.dependencies import (
    AuthenticatedRequestDependencies,
    get_request_dependencies,
)
from ring.search.crud.hybrid_search import (
    raw_search_documents,
    search,
)
from ring.search.models.hybrid_search import SearchableType
from ring.search.schemas.search import (
    RawSearchResponse,
    RawSearchResult,
    SearchHit,
    SearchResponse,
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
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_request_dependencies,
    ),
) -> RawSearchResponse:
    """Search the search table for a given query.

    Hits the caller cannot read are omitted (same authz as ``/search``).
    ``limit`` is applied after that filter; the SQL window overfetches so a
    page is not under-filled when unauthorized rows are dropped.

    Args:
        query: The search query string
        search_type: Type of search to perform (semantic, keyword, or dual)
        limit: Maximum number of results to return
        group_api_id: Optional group. Keeps that group and its letters,
            questions, and responses.
        participant_api_id: Optional responder. Keeps that person's responses.
        sort: Relevance (the search type's existing ranking) or entity time.
        req_dep: Authenticated request dependencies

    Returns:
        RawSearchResponse containing matching results and total count
    """
    if not query.strip():
        raise HTTPException(
            status_code=400, detail="Search query cannot be empty"
        )

    if search_type not in (
        SearchType.SEMANTIC,
        SearchType.KEYWORD,
        SearchType.DUAL,
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid search type. Must be one of: "
                f"{', '.join(t.value for t in SearchType)}"
            ),
        )

    authorized = raw_search_documents(
        db=req_dep.db,
        query=query,
        user=req_dep.current_user,
        limit=limit,
        search_type=search_type,
        group_api_id=group_api_id,
        participant_api_id=participant_api_id,
        sort=sort,
    )

    return RawSearchResponse(
        results=[
            RawSearchResult.model_validate(result) for result in authorized
        ],
        total=len(authorized),
    )


@router.get("/search", response_model=SearchResponse)
async def perform_search(
    query: str,
    search_type: SearchType = SearchType.KEYWORD,
    limit: int = 10,
    offset: int = 0,
    types: Annotated[list[SearchableType] | None, Query()] = None,
    group_api_id: str | None = None,
    participant_api_id: str | None = None,
    sort: SearchSort = SearchSort.RELEVANCE,
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

    ``group_api_id`` keeps that group plus its letters, questions, and
    responses. ``participant_api_id`` keeps responses by that person.
    ``sort`` is ``relevance`` (the search type's existing ranking),
    ``created_at_desc`` (newest entity), or ``created_at_asc`` (oldest).
    Hits the caller cannot read are omitted.
    """
    results = search(
        db=req_dep.db,
        query=query,
        user=req_dep.current_user,
        limit=limit,
        offset=offset,
        search_type=search_type,
        model_types=types,
        group_api_id=group_api_id,
        participant_api_id=participant_api_id,
        sort=sort,
    )
    return SearchResponse(
        results=[SearchHit.from_model(result) for result in results],
        total=len(results),
    )
