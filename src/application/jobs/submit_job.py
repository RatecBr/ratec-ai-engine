from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.domain.entities.job import Job
from src.domain.interfaces.job_repository import IJobRepository
from src.domain.interfaces.workflow_engine import IWorkflowEngine


@dataclass
class SubmitJobInput:
    workflow_id: str
    input: dict[str, Any]


@dataclass
class SubmitJobOutput:
    job: Job


class SubmitJobUseCase:
    def __init__(self, job_repository: IJobRepository, workflow_engine: IWorkflowEngine) -> None:
        self._repo = job_repository
        self._engine = workflow_engine

    async def execute(self, data: SubmitJobInput) -> SubmitJobOutput:
        workflow = await self._engine.get_workflow(data.workflow_id)
        if workflow is None:
            raise ValueError(f"Workflow '{data.workflow_id}' not found")

        job = Job(workflow_id=data.workflow_id, input=data.input)
        await self._repo.save(job)

        job = await self._engine.execute(job, workflow)
        await self._repo.save(job)

        return SubmitJobOutput(job=job)
