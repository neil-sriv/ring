from fastapi import APIRouter

router = APIRouter()

internal = APIRouter(
    prefix="/internal",
    tags=["internal"],
)

from ring.api import *  # noqa: E402, F403, F401


@router.get("/")
async def root():
    return {"message": "Hello World!"}


@router.get("/hello")
async def hello():
    # task = hello_task.delay()
    # return {"task_id": task.id}
    # Group.__table__.create(engine)
    # Letter.__table__.create(engine)
    return {"message": "Hello World!"}
