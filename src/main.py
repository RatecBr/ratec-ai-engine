from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1 import health, jobs, models, pipelines, providers, workflows

app = FastAPI(
    title="RATEC AI ENGINE",
    description="Plataforma oficial de Inteligência Artificial da RATEC",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/v1")
app.include_router(jobs.router, prefix="/v1")
app.include_router(workflows.router, prefix="/v1")
app.include_router(pipelines.router, prefix="/v1")
app.include_router(providers.router, prefix="/v1")
app.include_router(models.router, prefix="/v1")


@app.get("/", include_in_schema=False)
async def root() -> dict:
    return {"name": "RATEC AI ENGINE", "version": "0.1.0", "docs": "/docs"}
