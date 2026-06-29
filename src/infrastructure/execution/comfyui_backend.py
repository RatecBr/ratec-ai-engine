from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

from src.domain.entities.execution import ExecutionContext, ExecutionResult, ExecutionStatus
from src.infrastructure.execution.base_backend import BaseExecutionBackend
from src.infrastructure.providers.comfyui.client import ComfyUIClient
from src.infrastructure.providers.comfyui.exceptions import ComfyUIError
from src.infrastructure.providers.comfyui.job_executor import ComfyUIJobExecutor
from src.infrastructure.providers.comfyui.result_parser import ComfyUIResultParser
from src.infrastructure.providers.comfyui.workflow_loader import ComfyUIWorkflowLoader

_WORKFLOWS_ROOT = Path(__file__).parents[3] / "workflows"


class ComfyUIBackend(BaseExecutionBackend):
    """
    Backend de execução que roteia jobs para uma instância do ComfyUI.
    O ExecutionManager não conhece detalhes da API do ComfyUI —
    toda a comunicação fica isolada dentro do ComfyUIJobExecutor.
    """

    def __init__(
        self,
        base_url: str,
        workflows_root: Path = _WORKFLOWS_ROOT,
    ) -> None:
        client = ComfyUIClient(base_url)
        loader = ComfyUIWorkflowLoader(workflows_root)
        parser = ComfyUIResultParser()
        self._executor = ComfyUIJobExecutor(client, loader, parser)

    @property
    def backend_id(self) -> str:
        return "comfyui"

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        start = time.monotonic()
        try:
            output = await self._executor.execute(
                workflow_id=context.capability,
                parameters=context.payload,
            )
        except ComfyUIError as exc:
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
            output=output,
            duration_ms=duration_ms,
            completed_at=datetime.now(timezone.utc),
        )

    async def health_check(self) -> bool:
        return await self._executor._client.health_check()

    def supports_strategy(self, strategy: str) -> bool:
        return strategy in ("auto", "comfyui")
