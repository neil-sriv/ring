from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
async def auth_status():
    """Stub endpoint for auth status"""
    return {"status": "authenticated"} 