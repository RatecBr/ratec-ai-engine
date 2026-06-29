from __future__ import annotations

from dataclasses import dataclass

from src.domain.entities.job import Job, JobStatus
from src.domain.interfaces.job_repository import IJobRepository


@dataclass
class ListJobsInput:
    status: JobStatus | None = None
    workflow_id: str | None = None
    limit: int = 50
    offset: int = 0


@dataclass
class ListJobsOutput:
    jobs: list[Job]
    total: int


class ListJobsUseCase:
    def __init__(self, job_repository: IJobRepository) -> None:
        self._repo = job_repository

    async def execute(self, data: ListJobsInput) -> ListJobsOutput:
        jobs = await self._repo.list(
            status=data.status,
            workflow_id=data.workflow_id,
            limit=data.limit,
            offset=data.offset,
        )
        return ListJobsOutput(jobs=jobs, total=len(jobs))
