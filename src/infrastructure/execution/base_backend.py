from __future__ import annotations

from abc import abstractmethod

from src.domain.entities.execution import ExecutionContext, ExecutionResult
from src.domain.interfaces.execution_backend import IExecutionBackend


class BaseExecutionBackend(IExecutionBackend):
    @abstractmethod
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...

    def supports_strategy(self, strategy: str) -> bool:
        return strategy in ("auto", self.backend_id)
