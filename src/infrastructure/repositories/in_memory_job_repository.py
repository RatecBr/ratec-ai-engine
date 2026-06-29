from __future__ import annotations

import asyncio
from typing import Any

from src.domain.entities.job import Job, JobStatus
from src.domain.interfaces.job_repository import IJobRepository


class InMemoryJobRepository(IJobRepository):
    def __init__(self) -> None:
        self._store: dict[str, Job] = {}
        self._lock = asyncio.Lock()

    async def save(self, job: Job) -> Job:
        async with self._lock:
            self._store[job.id] = job
        return job

    async def get_by_id(self, job_id: str) -> Job | None:
        return self._store.get(job_id)

    async def list(
        self,
        status: JobStatus | None = None,
        workflow_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Job]:
        jobs = list(self._store.values())
        if status is not None:
            jobs = [j for j in jobs if j.status == status]
        if workflow_id is not None:
            jobs = [j for j in jobs if j.workflow_id == workflow_id]
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[offset : offset + limit]

    async def delete(self, job_id: str) -> bool:
        async with self._lock:
            if job_id in self._store:
                del self._store[job_id]
                return True
        return False
