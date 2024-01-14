from ring.fast import app, engine
from ring.postgres_models.group_model import Group


@app.get("/")
async def root():
    return {"message": "Hello World!"}


@app.get("/hello")
async def hello():
    # task = hello_task.delay()
    # return {"task_id": task.id}
    Group.__table__.create(engine)
    return {"message": "Hello World!"}
