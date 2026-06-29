from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.execution import ExecutionContext, ExecutionResult


class IExecutionBackend(ABC):
    @property
    @abstractmethod
    def backend_id(self) -> str:
        ...

    @abstractmethod
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...

    @abstractmethod
    def supports_strategy(self, strategy: str) -> bool:
        ...
