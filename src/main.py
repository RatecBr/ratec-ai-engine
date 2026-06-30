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

# Admin API
from src.api.admin import (
    health as admin_health,
    runtime as admin_runtime,
    system as admin_system,
    gpu as admin_gpu,
    storage as admin_storage,
    logs as admin_logs,
    metrics as admin_metrics,
    models as admin_models,
    workflows as admin_workflows
)

app.include_router(admin_health.router, prefix="/admin")
app.include_router(admin_runtime.router, prefix="/admin")
app.include_router(admin_system.router, prefix="/admin")
app.include_router(admin_gpu.router, prefix="/admin")
app.include_router(admin_storage.router, prefix="/admin")
app.include_router(admin_logs.router, prefix="/admin")
app.include_router(admin_metrics.router, prefix="/admin")
app.include_router(admin_models.router, prefix="/admin")
app.include_router(admin_workflows.router, prefix="/admin")

@app.get("/", include_in_schema=False)
async def root() -> dict:
    return {"name": "RATEC AI ENGINE", "version": "0.1.0", "docs": "/docs"}
