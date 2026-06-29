from __future__ import annotations

from src.domain.entities.pipeline import Pipeline
from src.domain.interfaces.pipeline_registry import IPipelineRegistry


class GetPipelineUseCase:
    def __init__(self, pipeline_registry: IPipelineRegistry) -> None:
        self._registry = pipeline_registry

    async def execute(self, pipeline_id: str) -> Pipeline:
        pipeline = self._registry.get(pipeline_id)
        if pipeline is None:
            raise ValueError(f"Pipeline '{pipeline_id}' not found")
        return pipeline
