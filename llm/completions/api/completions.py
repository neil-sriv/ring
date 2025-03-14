from fastapi import APIRouter

from llm.ai_client.ai_client import ai_client
from llm.completions.schemas.completions import (
    CompletionRequest,
    CompletionResponse,
)
from llm.lib.logger import logger

router = APIRouter()


def _get_model(prompt: str) -> str:
    return "deepseek-r1:7b"


@router.post("/generate", response_model=CompletionResponse)
async def generate_completion(request: CompletionRequest):
    """Stub endpoint for text completion generation"""
    logger.info(f"Request: {request}")
    model = _get_model(request.prompt)
    logger.info(f"Model: {model}")
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
    completion = await ai_client.completions.create(
        model="llama2",
        prompt="Say exactly 'Hello World' and nothing else",
        max_tokens=2,
    )
    return CompletionResponse(
        text=completion.choices[0].text,
        usage=completion.usage.model_dump(),
    )
