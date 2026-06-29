from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.domain.entities.job import Job
from src.domain.entities.workflow import Workflow


class IWorkflowEngine(ABC):
    @abstractmethod
    async def execute(self, job: Job, workflow: Workflow) -> Job:
        ...

    @abstractmethod
    async def get_workflow(self, workflow_id: str) -> Workflow | None:
        ...

    @abstractmethod
    async def list_workflows(self) -> list[Workflow]:
        ...
