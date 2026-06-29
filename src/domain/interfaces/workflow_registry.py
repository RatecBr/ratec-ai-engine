from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.workflow import Workflow


class IWorkflowRegistry(ABC):
    @abstractmethod
    def register(self, workflow: Workflow) -> None:
        ...

    @abstractmethod
    def get(self, workflow_id: str) -> Workflow | None:
        ...

    @abstractmethod
    def list_all(self) -> list[Workflow]:
        ...
