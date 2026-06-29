from __future__ import annotations

import time
from datetime import datetime, timezone

from src.domain.entities.execution import ExecutionContext, ExecutionResult, ExecutionStatus
from src.infrastructure.execution.base_backend import BaseExecutionBackend


class LocalBackend(BaseExecutionBackend):
    """Execução local para desenvolvimento e testes. Faz echo do payload."""

    @property
    def backend_id(self) -> str:
        return "local"

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        start = time.monotonic()
        output = {
            "echo": context.payload,
            "action": context.action,
            "capability": context.capability,
            "model_id": context.model_id,
        }
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
        return True

    def supports_strategy(self, strategy: str) -> bool:
        return strategy in ("auto", "local")
