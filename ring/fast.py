from fastapi import FastAPI

from ring.config import get_config
from ring.routes import router
from starlette.middleware.cors import CORSMiddleware

ring_config = get_config()
app = FastAPI(root_path=ring_config.root_path)

if ring_config.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(origin).strip("/")
            for origin in ring_config.BACKEND_CORS_ORIGINS
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(router)
