from __future__ import annotations

from dataclasses import dataclass

from src.domain.entities.job import Job
from src.domain.interfaces.job_repository import IJobRepository


@dataclass
class GetJobStatusOutput:
    job: Job


class GetJobStatusUseCase:
    def __init__(self, job_repository: IJobRepository) -> None:
        self._repo = job_repository

    async def execute(self, job_id: str) -> GetJobStatusOutput:
        job = await self._repo.get_by_id(job_id)
        if job is None:
            raise ValueError(f"Job '{job_id}' not found")
        return GetJobStatusOutput(job=job)
