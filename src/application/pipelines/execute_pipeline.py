from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.domain.entities.job import Job
from src.domain.interfaces.pipeline_engine import IPipelineEngine
from src.domain.interfaces.pipeline_registry import IPipelineRegistry


@dataclass
class ExecutePipelineInput:
    job: Job
    pipeline_id: str
    input_data: dict[str, Any]


@dataclass
class ExecutePipelineOutput:
    output: dict[str, Any]


class ExecutePipelineUseCase:
    def __init__(self, pipeline_engine: IPipelineEngine, pipeline_registry: IPipelineRegistry) -> None:
        self._engine = pipeline_engine
        self._registry = pipeline_registry

    async def execute(self, data: ExecutePipelineInput) -> ExecutePipelineOutput:
        pipeline = self._registry.get(data.pipeline_id)
        if pipeline is None:
            raise ValueError(f"Pipeline '{data.pipeline_id}' not found")
        output = await self._engine.execute(data.job, pipeline, data.input_data)
        return ExecutePipelineOutput(output=output)
