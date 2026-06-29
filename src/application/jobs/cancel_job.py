from __future__ import annotations

from src.domain.entities.job import Job, JobStatus
from src.domain.interfaces.job_repository import IJobRepository


class CancelJobUseCase:
    def __init__(self, job_repository: IJobRepository) -> None:
        self._repo = job_repository

    async def execute(self, job_id: str) -> Job:
        job = await self._repo.get_by_id(job_id)
        if job is None:
            raise ValueError(f"Job '{job_id}' not found")
        if job.is_terminal:
            raise ValueError(f"Job '{job_id}' is already in terminal state '{job.status}'")

        job.mark_cancelled()
        await self._repo.save(job)
        return job
