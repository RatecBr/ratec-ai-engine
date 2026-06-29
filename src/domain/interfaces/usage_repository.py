from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.usage import UsageRecord


class IUsageRepository(ABC):
    @abstractmethod
    async def record(self, usage: UsageRecord) -> UsageRecord:
        ...

    @abstractmethod
    async def list_by_job(self, job_id: str) -> list[UsageRecord]:
        ...

    @abstractmethod
    async def list_by_app(self, app_id: str, limit: int = 100) -> list[UsageRecord]:
        ...
