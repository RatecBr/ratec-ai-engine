from __future__ import annotations

from abc import abstractmethod
from typing import Any

from src.domain.entities.provider import Provider
from src.domain.interfaces.provider import IProvider


class BaseProvider(IProvider):
    def __init__(self, provider_info: Provider) -> None:
        self._info = provider_info

    def get_info(self) -> Provider:
        return self._info

    @abstractmethod
    async def run(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        ...

    @abstractmethod
    async def get_job_status(self, provider_job_id: str) -> dict[str, Any]:
        ...

    @abstractmethod
    async def cancel_job(self, provider_job_id: str) -> bool:
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...
