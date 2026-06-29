from __future__ import annotations

import uuid
from typing import Any

from src.domain.entities.provider import Provider, ProviderType
from src.infrastructure.providers.base_provider import BaseProvider


class LocalProvider(BaseProvider):
    """Stub provider for local development and testing."""

    def __init__(self) -> None:
        super().__init__(
            Provider(
                id="local",
                name="Local (Development)",
                type=ProviderType.LOCAL,
                capabilities=["echo", "mock"],
            )
        )
        self._jobs: dict[str, dict[str, Any]] = {}

    async def run(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        job_id = str(uuid.uuid4())
        result = {"id": job_id, "status": "COMPLETED", "output": {"echo": payload, "action": action}}
        self._jobs[job_id] = result
        return result

    async def get_job_status(self, provider_job_id: str) -> dict[str, Any]:
        return self._jobs.get(provider_job_id, {"id": provider_job_id, "status": "NOT_FOUND"})

    async def cancel_job(self, provider_job_id: str) -> bool:
        return provider_job_id in self._jobs

    async def health_check(self) -> bool:
        return True
