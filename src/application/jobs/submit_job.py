from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.domain.entities.job import Job
from src.domain.interfaces.job_repository import IJobRepository
from src.domain.interfaces.workflow_engine import IWorkflowEngine
from src.domain.interfaces.workflow_registry import IWorkflowRegistry


@dataclass
class SubmitJobInput:
    workflow_id: str
    input: dict[str, Any]


@dataclass
class SubmitJobOutput:
    job: Job


class SubmitJobUseCase:
    def __init__(
        self,
        job_repository: IJobRepository,
        workflow_engine: IWorkflowEngine,
        workflow_registry: IWorkflowRegistry,
    ) -> None:
        self._repo = job_repository
        self._engine = workflow_engine
        self._workflow_registry = workflow_registry

    async def execute(self, data: SubmitJobInput) -> SubmitJobOutput:
        workflow = self._workflow_registry.get(data.workflow_id)
        if workflow is None:
            raise ValueError(f"Workflow '{data.workflow_id}' not found")

        job = Job(workflow_id=data.workflow_id, input=data.input)
        await self._repo.save(job)

        job = await self._engine.execute(job, workflow)
        await self._repo.save(job)

        return SubmitJobOutput(job=job)
