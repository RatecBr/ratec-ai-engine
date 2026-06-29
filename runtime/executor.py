from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

import httpx

from runtime.configuration import RuntimeConfig


class ComfyUIExecutor:
    """
    Gerencia o ciclo completo de execução de um job no ComfyUI:
    submit → poll → parse result.
    Toda a comunicação com a API do ComfyUI permanece isolada aqui.
    """

    def __init__(self, config: RuntimeConfig) -> None:
        self._config = config
        self._client_id = str(uuid.uuid4())

    async def submit(self, client: httpx.AsyncClient, workflow: dict[str, Any]) -> str:
        """Submete um workflow ao ComfyUI. Retorna o prompt_id."""
        r = await client.post(
            f"{self._config.comfyui_url}/prompt",
            json={"prompt": workflow, "client_id": self._client_id},
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        if data.get("node_errors"):
            raise RuntimeError(f"Erros nos nodes do workflow: {data['node_errors']}")
        return data["prompt_id"]

    async def poll(
        self,
        client: httpx.AsyncClient,
        prompt_id: str,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """Aguarda conclusão via polling do histórico. Retorna o history entry."""
        effective_timeout = timeout or self._config.job_timeout
        deadline = time.monotonic() + effective_timeout
        while time.monotonic() < deadline:
            r = await client.get(
                f"{self._config.comfyui_url}/history/{prompt_id}",
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()
            if prompt_id in data:
                return data[prompt_id]
            await asyncio.sleep(self._config.poll_interval)
        raise TimeoutError(f"Job '{prompt_id}' não completou em {effective_timeout}s")

    def parse_images(self, history_entry: dict[str, Any]) -> list[dict[str, Any]]:
        """Extrai a lista de imagens geradas a partir do histórico do ComfyUI."""
        images = []
        for node_id, node_output in history_entry.get("outputs", {}).items():
            for img in node_output.get("images", []):
                images.append({
                    "filename": img.get("filename", ""),
                    "subfolder": img.get("subfolder", ""),
                    "type": img.get("type", "output"),
                    "node_id": node_id,
                })
        return images
