from __future__ import annotations

from src.domain.entities.workflow import Workflow
from src.domain.interfaces.workflow_engine import IWorkflowEngine


class GetWorkflowUseCase:
    def __init__(self, workflow_engine: IWorkflowEngine) -> None:
        self._engine = workflow_engine

    async def execute(self, workflow_id: str) -> Workflow:
        workflow = await self._engine.get_workflow(workflow_id)
        if workflow is None:
            raise ValueError(f"Workflow '{workflow_id}' not found")
        return workflow
