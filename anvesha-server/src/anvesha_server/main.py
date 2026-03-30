from __future__ import annotations

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from anvesha_server.api import api_router
from anvesha_server.config import get_settings
from anvesha_server.db.engine import dispose_db, init_db

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield
    await dispose_db()


app = FastAPI(
    title="Anvesha Server",
    version="0.1.0",
    summary="Tracing-first OTLP backend for Yuktha observability.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/v1")


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
async def root() -> dict[str, object]:
    return {
        "name": "Anvesha Server",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/healthz",
        "apiPrefix": "/v1",
    }


def main() -> None:
    uvicorn.run(
        "anvesha_server.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level=settings.log_level,
    )


if __name__ == "__main__":
    main()
