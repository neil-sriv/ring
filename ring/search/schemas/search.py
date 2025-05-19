from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel


class RawSearchResult(BaseModel):
    raw_text: str

    class Config:
        from_attributes = True


class RawSearchResponse(BaseModel):
    results: List[RawSearchResult]
    total: int


class SearchResult(BaseModel):
    model_api_identifier: str


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int


class SearchType(str, Enum):
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    DUAL = "dual"
