from __future__ import annotations

from dataclasses import dataclass

from src.domain.entities.workflow import Workflow
from src.domain.interfaces.workflow_registry import IWorkflowRegistry


@dataclass
class ListWorkflowsOutput:
    workflows: list[Workflow]


class ListWorkflowsUseCase:
    def __init__(self, workflow_registry: IWorkflowRegistry) -> None:
        self._registry = workflow_registry

    async def execute(self) -> ListWorkflowsOutput:
        return ListWorkflowsOutput(workflows=self._registry.list_all())
