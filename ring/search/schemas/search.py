from __future__ import annotations

from typing import List

from pydantic import BaseModel


class SearchResult(BaseModel):
    raw_text: str

    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
