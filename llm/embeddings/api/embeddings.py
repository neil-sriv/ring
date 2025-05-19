from __future__ import annotations

from fastapi import APIRouter

from llm.ai_client.ai_client import (
    LLMType,
    get_llm,
)
from llm.embeddings.schemas.embeddings import (
    EmbeddingRequest,
    EmbeddingResponse,
)
from llm.lib.logger import logger

router = APIRouter()


@router.post("/embed", response_model=EmbeddingResponse)
async def embed(request: EmbeddingRequest):
    """Stub endpoint for text completion generation"""
    llm = get_llm(LLMType.GEMINI, "embeddings")
    logger.info(f"Embedding request: {request}")
    embedding = await llm.client.embeddings.create(
        model=llm.model,
        input=request.text,
    )
    return EmbeddingResponse(
        embedding=embedding.data[0].embedding,
    )


@router.post("/test", response_model=EmbeddingResponse)
async def test_completion():
    """Test endpoint that returns an embedding for a test text"""
    llm = get_llm(LLMType.GEMINI, "embeddings")
    embedding = await llm.client.embeddings.create(
        model=llm.model,
        input="Hello World",
    )
    return EmbeddingResponse(
        embedding=embedding.data[0].embedding,
    )
