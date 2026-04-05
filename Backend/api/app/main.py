"""
Arkon API — threads, auth, settings, governance engine, share, artifacts.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import artifacts_dl, auth, planning, settings as settings_r, share, threads, users

from .core.config import settings
from .db.session import init_db
from .routers import (
    ws_jobs,
)
from .services import planning_ws


@asynccontextmanager
async def lifespan(app: FastAPI):
    planning_ws.set_main_loop(asyncio.get_running_loop())
    init_db()
    yield
    planning_ws.set_main_loop(None)


app = FastAPI(title="Arkon Governance API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins if o.strip()] or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


prefix = "/v1"
app.include_router(auth.router, prefix=prefix)
app.include_router(users.router, prefix=prefix)
app.include_router(settings_r.router, prefix=prefix)
app.include_router(threads.router, prefix=prefix)
app.include_router(planning.router, prefix=prefix)
app.include_router(share.router, prefix=prefix)
app.include_router(artifacts_dl.router, prefix=prefix)
app.include_router(ws_jobs.router, prefix=prefix)
