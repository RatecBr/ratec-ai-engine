from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.job import Job
from src.domain.entities.workflow import Workflow


class IWorkflowEngine(ABC):
    @abstractmethod
    async def execute(self, job: Job, workflow: Workflow) -> Job:
        ...
