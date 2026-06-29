from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

import httpx

from src.domain.entities.execution import ExecutionContext, ExecutionResult, ExecutionStatus
from src.infrastructure.execution.base_backend import BaseExecutionBackend


class RunPodBackend(BaseExecutionBackend):
    """Execução via RunPod Serverless. Backend de produção inicial."""

    def __init__(self, api_key: str, endpoint_id: str) -> None:
        self._api_key = api_key
        self._endpoint_id = endpoint_id
        self._base_url = f"https://api.runpod.ai/v2/{endpoint_id}"

    @property
    def backend_id(self) -> str:
        return "runpod"

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{self._base_url}/runsync",
                    json={
                        "input": {
                            "capability": context.capability,
                            "action": context.action,
                            "model_id": context.model_id,
                            **context.payload,
                        }
                    },
                    headers=self._headers(),
                )
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            duration_ms = int((time.monotonic() - start) * 1000)
            return ExecutionResult(
                execution_id=context.id,
                backend=self.backend_id,
                status=ExecutionStatus.FAILED,
                error=str(exc),
                duration_ms=duration_ms,
                completed_at=datetime.now(timezone.utc),
            )

        duration_ms = int((time.monotonic() - start) * 1000)
        return ExecutionResult(
            execution_id=context.id,
            backend=self.backend_id,
            status=ExecutionStatus.COMPLETED,
            output=data.get("output", data),
            duration_ms=duration_ms,
            completed_at=datetime.now(timezone.utc),
        )

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(f"{self._base_url}/health", headers=self._headers())
                return r.status_code == 200
        except Exception:
            return False

    def supports_strategy(self, strategy: str) -> bool:
        return strategy in ("auto", "serverless", "runpod")
