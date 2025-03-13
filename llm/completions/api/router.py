from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class CompletionRequest(BaseModel):
    prompt: str
    max_tokens: int = 100


class CompletionResponse(BaseModel):
    text: str
    usage: dict


@router.post("/generate", response_model=CompletionResponse)
async def generate_completion(request: CompletionRequest):
    """Stub endpoint for text completion generation"""
    return CompletionResponse(
        text="This is a stub completion response",
        usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    )
