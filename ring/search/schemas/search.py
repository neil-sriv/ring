from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class RawSearchResult(BaseModel):
    raw_text: str

    class Config:
        from_attributes = True


class RawSearchResponse(BaseModel):
    results: list[RawSearchResult]
    total: int


class SearchType(str, Enum):
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    DUAL = "dual"


class SearchSort(str, Enum):
    RELEVANCE = "relevance"
    CREATED_AT_DESC = "created_at_desc"
    CREATED_AT_ASC = "created_at_asc"
