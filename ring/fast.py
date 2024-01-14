from fastapi import FastAPI

from ring.config import get_config
from ring.routes import router

app = FastAPI()
ring_config = get_config()

app.include_router(router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)  # type: ignore
