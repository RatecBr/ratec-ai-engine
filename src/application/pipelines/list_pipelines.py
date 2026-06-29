from __future__ import annotations

from dataclasses import dataclass

from src.domain.entities.pipeline import Pipeline
from src.domain.interfaces.pipeline_registry import IPipelineRegistry


@dataclass
class ListPipelinesOutput:
    pipelines: list[Pipeline]


class ListPipelinesUseCase:
    def __init__(self, pipeline_registry: IPipelineRegistry) -> None:
        self._registry = pipeline_registry

    async def execute(self) -> ListPipelinesOutput:
        return ListPipelinesOutput(pipelines=self._registry.list_all())
