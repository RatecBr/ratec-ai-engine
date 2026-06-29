from __future__ import annotations

import asyncio

from src.domain.entities.usage import UsageRecord
from src.domain.interfaces.usage_repository import IUsageRepository


class InMemoryUsageRepository(IUsageRepository):
    def __init__(self) -> None:
        self._records: list[UsageRecord] = []
        self._lock = asyncio.Lock()

    async def record(self, usage: UsageRecord) -> UsageRecord:
        async with self._lock:
            self._records.append(usage)
        return usage

    async def list_by_job(self, job_id: str) -> list[UsageRecord]:
        return [r for r in self._records if r.job_id == job_id]

    async def list_by_app(self, app_id: str, limit: int = 100) -> list[UsageRecord]:
        return [r for r in self._records if r.app_id == app_id][:limit]
