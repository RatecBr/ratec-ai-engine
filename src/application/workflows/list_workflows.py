from __future__ import annotations

from dataclasses import dataclass

from src.domain.entities.workflow import Workflow
from src.domain.interfaces.workflow_engine import IWorkflowEngine


@dataclass
class ListWorkflowsOutput:
    workflows: list[Workflow]


class ListWorkflowsUseCase:
    def __init__(self, workflow_engine: IWorkflowEngine) -> None:
        self._engine = workflow_engine

    async def execute(self) -> ListWorkflowsOutput:
        workflows = await self._engine.list_workflows()
        return ListWorkflowsOutput(workflows=workflows)
