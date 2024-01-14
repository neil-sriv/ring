from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from ring.config import get_config
from ring.postgres_models.group_model import Group

# from ring.config import get_config
# from ring.worker import hello_task

# ring_config = get_config()
app = FastAPI()
ring_config = get_config()


engine = create_engine(
    ring_config.sqlalchemy_database_uri, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


@app.get("/")
async def root():
    return {"message": "Hello World!"}


@app.get("/hello")
async def hello():
    # task = hello_task.delay()
    # return {"task_id": task.id}
    Group.__table__.create(engine)
    return {"message": "Hello World!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)  # type: ignore
