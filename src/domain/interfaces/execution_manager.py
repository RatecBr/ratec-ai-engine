from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.execution import ExecutionContext, ExecutionResult
from src.domain.interfaces.execution_backend import IExecutionBackend


class IExecutionManager(ABC):
    @abstractmethod
    def register_backend(self, backend: IExecutionBackend) -> None:
        ...

    @abstractmethod
    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        ...

    @abstractmethod
    def list_backends(self) -> list[IExecutionBackend]:
        ...
