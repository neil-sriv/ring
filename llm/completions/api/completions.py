from __future__ import annotations

from fastapi import APIRouter

from llm.ai_client.ai_client import (
    LLMType,
    get_llm,
)
from llm.completions.schemas.completions import (
    CompletionRequest,
    CompletionResponse,
)
from llm.lib.logger import logger

router = APIRouter()


@router.post("/generate", response_model=CompletionResponse)
async def generate_completion(request: CompletionRequest):
    """Stub endpoint for text completion generation"""
    llm = get_llm(LLMType.OPENAI)
    completion = await llm.client.chat.completions.create(
        model=llm.model,
        messages=[
            {
                "role": "user",
                "content": request.prompt,
            }
        ],
        max_tokens=request.max_tokens,
        response_format=request.output_schema,
    )
    logger.info(f"Completion: {completion}")
    return CompletionResponse(
        completion=completion,
        text=completion.choices[0].message.content,
        usage=completion.usage,
    )


@router.post("/test", response_model=CompletionResponse)
async def test_completion():
    """Test endpoint that returns a simple Hello World completion"""
    prompt = "Say exactly 'Hello World' and nothing else"
    llm = get_llm(LLMType.GEMINI)
    completion = await llm.client.chat.completions.create(
        model=llm.model,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        max_tokens=2,
    )
    return CompletionResponse(
        completion=completion,
        text=completion.choices[0].message.content,
        usage=completion.usage,
    )
