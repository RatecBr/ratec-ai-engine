from __future__ import annotations

from fastapi import APIRouter, Depends

from src.api.v1.schemas import HealthResponse
from src.config.dependencies import get_execution_manager, get_provider_registry

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health(
    registry=Depends(get_provider_registry),
    execution_manager=Depends(get_execution_manager),
) -> HealthResponse:
    provider_statuses: dict[str, str] = {}
    for provider in registry.list_all():
        info = provider.get_info()
        is_healthy = await provider.health_check()
        provider_statuses[info.id] = "ok" if is_healthy else "degraded"

    backend_statuses: dict[str, str] = {}
    for backend in execution_manager.list_backends():
        is_healthy = await backend.health_check()
        backend_statuses[backend.backend_id] = "ok" if is_healthy else "degraded"

    all_ok = all(v == "ok" for v in {**provider_statuses, **backend_statuses}.values())
    overall = "ok" if all_ok else "degraded"

    return HealthResponse(
        status=overall,
        version="0.1.0",
        providers=provider_statuses,
        backends=backend_statuses,
    )
