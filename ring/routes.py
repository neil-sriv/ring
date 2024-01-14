from fastapi import APIRouter
from ring.postgres_models.group_model import Group
from ring.sqlalchemy_base import engine

router = APIRouter()


@router.get("/")
async def root():
    return {"message": "Hello World!"}


@router.get("/hello")
async def hello():
    # task = hello_task.delay()
    # return {"task_id": task.id}
    Group.__table__.create(engine)
    return {"message": "Hello World!"}
