from __future__ import annotations

from typing import Any

from src.domain.entities.provider import Provider, ProviderType
from src.infrastructure.providers.base_provider import BaseProvider
from src.infrastructure.providers.comfyui.client import ComfyUIClient


class ComfyUIProvider(BaseProvider):
    """
    Representa o ComfyUI no catálogo de providers do RATEC AI ENGINE (/v1/providers).
    A execução real é delegada ao ComfyUIBackend via ExecutionManager.
    """

    def __init__(self, base_url: str) -> None:
        super().__init__(
            Provider(
                id="comfyui",
                name="ComfyUI",
                type=ProviderType.COMFYUI,
                capabilities=[
                    "image-generation",
                    "inpainting",
                    "image-to-image",
                    "upscaling",
                ],
            )
        )
        self._client = ComfyUIClient(base_url)

    async def run(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError(
            "Use o ExecutionManager para executar via ComfyUI."
        )

    async def get_job_status(self, provider_job_id: str) -> dict[str, Any]:
        history = await self._client.get_history(provider_job_id)
        entry = history.get(provider_job_id, {})
        status_data = entry.get("status", {})
        return {
            "id": provider_job_id,
            "status": "COMPLETED" if status_data.get("completed") else "RUNNING",
            "messages": status_data.get("messages", []),
        }

    async def cancel_job(self, provider_job_id: str) -> bool:
        return False

    async def health_check(self) -> bool:
        return await self._client.health_check()
