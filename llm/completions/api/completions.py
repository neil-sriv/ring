from fastapi import APIRouter

from llm.ai_client.ai_client import ai_client
from llm.completions.schemas.completions import (
    CompletionRequest,
    CompletionResponse,
)

router = APIRouter()


@router.post("/generate", response_model=CompletionResponse)
async def generate_completion(request: CompletionRequest):
    """Stub endpoint for text completion generation"""
    return CompletionResponse(
        text="This is a stub completion response",
        usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
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
