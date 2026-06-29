from __future__ import annotations

from typing import Any

from src.domain.entities.provider import Provider, ProviderType
from src.infrastructure.providers.base_provider import BaseProvider


class LocalProvider(BaseProvider):
    """Representa a capability local no catálogo de providers (dev/testing)."""

    def __init__(self) -> None:
        super().__init__(
            Provider(
                id="local",
                name="Local (Development)",
                type=ProviderType.LOCAL,
                capabilities=["echo", "mock"],
            )
        )

    async def run(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {"echo": payload, "action": action}

    async def get_job_status(self, provider_job_id: str) -> dict[str, Any]:
        return {"id": provider_job_id, "status": "COMPLETED"}

    async def cancel_job(self, provider_job_id: str) -> bool:
        return True

    async def health_check(self) -> bool:
        return True
