from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def auth_status():
    """Check authentication status"""
    return {"status": "authenticated", "message": "API key is valid"}
