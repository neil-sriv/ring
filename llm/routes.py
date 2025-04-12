from __future__ import annotations

from fastapi import APIRouter

from llm.auth.api.auth import router as auth_router
from llm.completions.api.completions import router as completions_router
from llm.rag.api.rag import router as rag_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(
    completions_router, prefix="/completions", tags=["completions"]
)
router.include_router(rag_router, prefix="/rag", tags=["rag"])
