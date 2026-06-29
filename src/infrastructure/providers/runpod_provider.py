from __future__ import annotations

from typing import Any

import httpx

from src.domain.entities.provider import Provider, ProviderType
from src.infrastructure.providers.base_provider import BaseProvider


class RunPodProvider(BaseProvider):
    """Representa a capability RunPod no catálogo de providers.
    A execução real ocorre via RunPodBackend na camada de infrastructure/execution."""

    def __init__(self, api_key: str, endpoint_id: str) -> None:
        super().__init__(
            Provider(
                id="runpod",
                name="RunPod Serverless",
                type=ProviderType.RUNPOD,
                capabilities=["image-generation", "inference", "custom"],
            )
        )
        self._api_key = api_key
        self._endpoint_id = endpoint_id
        self._base_url = f"https://api.runpod.ai/v2/{endpoint_id}"

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}

    async def run(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{self._base_url}/runsync",
                json={"input": {"action": action, **payload}},
                headers=self._headers(),
            )
            r.raise_for_status()
            return r.json()

    async def get_job_status(self, provider_job_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(f"{self._base_url}/status/{provider_job_id}", headers=self._headers())
            r.raise_for_status()
            return r.json()

    async def cancel_job(self, provider_job_id: str) -> bool:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(f"{self._base_url}/cancel/{provider_job_id}", headers=self._headers())
            return r.status_code == 200

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(f"{self._base_url}/health", headers=self._headers())
                return r.status_code == 200
        except Exception:
            return False
