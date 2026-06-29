from __future__ import annotations

from fastapi import APIRouter, Depends

from src.api.v1.schemas import HealthResponse
from src.config.dependencies import get_provider_registry

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health(registry=Depends(get_provider_registry)) -> HealthResponse:
    provider_statuses: dict[str, str] = {}
    for provider in registry.list_all():
        info = provider.get_info()
        is_healthy = await provider.health_check()
        provider_statuses[info.id] = "ok" if is_healthy else "degraded"

    overall = "ok" if all(v == "ok" for v in provider_statuses.values()) else "degraded"
    return HealthResponse(status=overall, version="0.1.0", providers=provider_statuses)
