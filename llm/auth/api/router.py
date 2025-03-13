from fastapi import APIRouter, Depends, Request

from llm.dependencies import (
    AuthenticatedRequestDependencies,
    get_authenticated_request_dependencies,
)

router = APIRouter()

@router.get("/status")
async def auth_status(
    req_dep: AuthenticatedRequestDependencies = Depends(
        get_authenticated_request_dependencies
    ),
):
    """Check authentication status"""
    return {"status": "authenticated", "message": "API key is valid"}
