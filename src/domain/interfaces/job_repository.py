from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.domain.entities.job import Job, JobStatus


class IJobRepository(ABC):
    @abstractmethod
    async def save(self, job: Job) -> Job:
        ...

    @abstractmethod
    async def get_by_id(self, job_id: str) -> Job | None:
        ...

    @abstractmethod
    async def list(
        self,
        status: JobStatus | None = None,
        workflow_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Job]:
        ...

    @abstractmethod
    async def delete(self, job_id: str) -> bool:
        ...
