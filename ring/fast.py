from fastapi import FastAPI

from ring.config import get_config
from ring.routes import router, internal

ring_config = get_config()
app = FastAPI(root_path=ring_config.root_path)

app.include_router(router)
app.include_router(internal)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)  # type: ignore
