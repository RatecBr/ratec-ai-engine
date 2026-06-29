from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.domain.entities.job import Job
from src.domain.entities.pipeline import Pipeline


class IPipelineEngine(ABC):
    @abstractmethod
    async def execute(self, job: Job, pipeline: Pipeline, input_data: dict[str, Any]) -> dict[str, Any]:
        ...
