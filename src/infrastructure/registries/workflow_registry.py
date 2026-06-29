from __future__ import annotations

from src.domain.entities.workflow import Workflow
from src.domain.interfaces.workflow_registry import IWorkflowRegistry


class WorkflowRegistry(IWorkflowRegistry):
    def __init__(self) -> None:
        self._workflows: dict[str, Workflow] = {}

    def register(self, workflow: Workflow) -> None:
        self._workflows[workflow.id] = workflow

    def get(self, workflow_id: str) -> Workflow | None:
        return self._workflows.get(workflow_id)

    def list_all(self) -> list[Workflow]:
        return list(self._workflows.values())
