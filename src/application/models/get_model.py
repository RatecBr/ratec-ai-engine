from __future__ import annotations

from src.domain.entities.model import AIModel
from src.domain.interfaces.model_registry import IModelRegistry


class GetModelUseCase:
    def __init__(self, model_registry: IModelRegistry) -> None:
        self._registry = model_registry

    async def execute(self, model_id: str) -> AIModel:
        model = self._registry.get(model_id)
        if model is None:
            raise ValueError(f"Model '{model_id}' not found")
        return model
