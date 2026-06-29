from __future__ import annotations

import uuid
from typing import Any

import httpx

from src.infrastructure.providers.comfyui.exceptions import ComfyUIConnectionError
from src.infrastructure.providers.comfyui.models import ComfyUIPromptResponse


class ComfyUIClient:
    """
    Cliente HTTP de baixo nível para a API do ComfyUI.
    Responsável exclusivamente pela comunicação HTTP — sem lógica de negócio.
    """

    def __init__(self, base_url: str, timeout: int = 30) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._client_id = str(uuid.uuid4())

    @property
    def client_id(self) -> str:
        return self._client_id

    async def submit_prompt(self, workflow: dict[str, Any]) -> ComfyUIPromptResponse:
        """Envia um workflow para execução. Retorna o prompt_id gerado pelo ComfyUI."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                r = await client.post(
                    f"{self._base_url}/prompt",
                    json={"prompt": workflow, "client_id": self._client_id},
                )
                r.raise_for_status()
                data = r.json()
                return ComfyUIPromptResponse(
                    prompt_id=data["prompt_id"],
                    number=data.get("number", 0),
                    node_errors=data.get("node_errors", {}),
                )
        except httpx.HTTPError as exc:
            raise ComfyUIConnectionError(f"Falha ao submeter prompt: {exc}") from exc

    async def get_history(self, prompt_id: str) -> dict[str, Any]:
        """Consulta o histórico de execução de um prompt. Retorna dict vazio se ainda em fila."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                r = await client.get(f"{self._base_url}/history/{prompt_id}")
                r.raise_for_status()
                return r.json()
        except httpx.HTTPError as exc:
            raise ComfyUIConnectionError(f"Falha ao consultar histórico de '{prompt_id}': {exc}") from exc

    async def get_queue(self) -> dict[str, Any]:
        """Retorna o estado atual da fila de execução do ComfyUI."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                r = await client.get(f"{self._base_url}/queue")
                r.raise_for_status()
                return r.json()
        except httpx.HTTPError as exc:
            raise ComfyUIConnectionError(f"Falha ao consultar fila: {exc}") from exc

    async def upload_image(
        self,
        image_data: bytes,
        filename: str,
        image_type: str = "input",
    ) -> dict[str, Any]:
        """Faz upload de uma imagem para uso em workflows. Reservado para uso futuro."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                r = await client.post(
                    f"{self._base_url}/upload/image",
                    files={"image": (filename, image_data, "image/png")},
                    data={"type": image_type},
                )
                r.raise_for_status()
                return r.json()
        except httpx.HTTPError as exc:
            raise ComfyUIConnectionError(f"Falha ao fazer upload da imagem: {exc}") from exc

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{self._base_url}/system_stats")
                return r.status_code == 200
        except Exception:
            return False
