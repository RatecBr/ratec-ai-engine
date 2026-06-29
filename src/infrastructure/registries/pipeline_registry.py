from __future__ import annotations

from src.domain.entities.pipeline import Pipeline
from src.domain.interfaces.pipeline_registry import IPipelineRegistry


class PipelineRegistry(IPipelineRegistry):
    def __init__(self) -> None:
        self._pipelines: dict[str, Pipeline] = {}

    def register(self, pipeline: Pipeline) -> None:
        self._pipelines[pipeline.id] = pipeline

    def get(self, pipeline_id: str) -> Pipeline | None:
        return self._pipelines.get(pipeline_id)

    def list_all(self) -> list[Pipeline]:
        return list(self._pipelines.values())
