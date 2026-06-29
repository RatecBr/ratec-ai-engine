from __future__ import annotations

from datetime import datetime, timezone

from src.domain.entities.execution import ExecutionContext, ExecutionResult, ExecutionStatus
from src.domain.interfaces.execution_backend import IExecutionBackend
from src.domain.interfaces.execution_manager import IExecutionManager


class ExecutionManager(IExecutionManager):
    """Roteia execuções para o backend mais adequado baseado na estratégia e disponibilidade."""

    _PRIORITY_ORDER = ("runpod", "comfyui", "modal", "replicate", "aws", "azure", "kubernetes")

    def __init__(self) -> None:
        self._backends: dict[str, IExecutionBackend] = {}

    def register_backend(self, backend: IExecutionBackend) -> None:
        self._backends[backend.backend_id] = backend

    def list_backends(self) -> list[IExecutionBackend]:
        return list(self._backends.values())

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        backend = self._resolve_backend(context.execution_strategy)
        if backend is None:
            return ExecutionResult(
                execution_id=context.id,
                backend="none",
                status=ExecutionStatus.FAILED,
                error=f"No backend available for strategy '{context.execution_strategy}'",
                completed_at=datetime.now(timezone.utc),
            )
        return await backend.execute(context)

    def _resolve_backend(self, strategy: str) -> IExecutionBackend | None:
        if strategy in self._backends:
            return self._backends[strategy]

        candidates = [b for b in self._backends.values() if b.supports_strategy(strategy)]
        if not candidates:
            return None

        for preferred in self._PRIORITY_ORDER:
            for b in candidates:
                if b.backend_id == preferred:
                    return b

        return candidates[0]
