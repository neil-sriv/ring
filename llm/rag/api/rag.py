from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class RAGRequest(BaseModel):
    query: str
    context_window: int = 2000


class RAGResponse(BaseModel):
    answer: str
    sources: list[str]
    usage: dict


@router.post("/query", response_model=RAGResponse)
async def query_rag(request: RAGRequest):
    """Stub endpoint for RAG query"""
    return RAGResponse(
        answer="This is a stub RAG response",
        sources=["source1", "source2"],
        usage={"tokens": 0, "sources_retrieved": 2},
    )
