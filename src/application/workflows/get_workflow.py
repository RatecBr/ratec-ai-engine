from __future__ import annotations

from src.domain.entities.workflow import Workflow
from src.domain.interfaces.workflow_registry import IWorkflowRegistry


class GetWorkflowUseCase:
    def __init__(self, workflow_registry: IWorkflowRegistry) -> None:
        self._registry = workflow_registry

    async def execute(self, workflow_id: str) -> Workflow:
        workflow = self._registry.get(workflow_id)
        if workflow is None:
            raise ValueError(f"Workflow '{workflow_id}' not found")
        return workflow
