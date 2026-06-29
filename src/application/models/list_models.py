from __future__ import annotations

from dataclasses import dataclass

from src.domain.entities.model import AIModel
from src.domain.interfaces.model_registry import IModelRegistry


@dataclass
class ListModelsOutput:
    models: list[AIModel]


class ListModelsUseCase:
    def __init__(self, model_registry: IModelRegistry) -> None:
        self._registry = model_registry

    async def execute(self, capability: str | None = None) -> ListModelsOutput:
        if capability:
            models = self._registry.list_by_capability(capability)
        else:
            models = self._registry.list_all()
        return ListModelsOutput(models=models)
