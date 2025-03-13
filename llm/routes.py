from fastapi import APIRouter

from llm.auth.api.router import router as auth_router
from llm.completions.api.router import router as completions_router
from llm.rag.api.router import router as rag_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(
    completions_router, prefix="/completions", tags=["completions"]
)
router.include_router(rag_router, prefix="/rag", tags=["rag"])
