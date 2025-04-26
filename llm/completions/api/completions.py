from __future__ import annotations

from fastapi import APIRouter

from llm.ai_client.ai_client import ai_client
from llm.completions.schemas.completions import (
    CompletionRequest,
    CompletionResponse,
)
from llm.lib.logger import logger

router = APIRouter()


def _get_model(prompt: str) -> str:
    model = "llama3.2"
    logger.info(f"Model: {model}")
    return model


@router.post("/generate", response_model=CompletionResponse)
async def generate_completion(request: CompletionRequest):
    """Stub endpoint for text completion generation"""
    model = _get_model(request.prompt)
    completion = await ai_client.completions.create(
        model=model,
        prompt=request.prompt,
        max_tokens=request.max_tokens,
    )
    logger.info(f"Completion: {completion}")
    return CompletionResponse(
        text=completion.choices[0].text,
        usage=completion.usage.model_dump(),
    )


@router.post("/test", response_model=CompletionResponse)
async def test_completion():
    """Test endpoint that returns a simple Hello World completion"""
    prompt = "Say exactly 'Hello World' and nothing else"
    model = _get_model(prompt)
    completion = await ai_client.completions.create(
        model=model,
        prompt=prompt,
        max_tokens=2,
    )
    return CompletionResponse(
        text=completion.choices[0].text,
        usage=completion.usage.model_dump(),
    )
