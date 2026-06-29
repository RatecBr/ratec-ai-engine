from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.pipeline import Pipeline


class IPipelineRegistry(ABC):
    @abstractmethod
    def register(self, pipeline: Pipeline) -> None:
        ...

    @abstractmethod
    def get(self, pipeline_id: str) -> Pipeline | None:
        ...

    @abstractmethod
    def list_all(self) -> list[Pipeline]:
        ...
