from __future__ import annotations

from src.domain.entities.model import AIModel
from src.domain.interfaces.model_registry import IModelRegistry


class ModelRegistry(IModelRegistry):
    def __init__(self) -> None:
        self._models: dict[str, AIModel] = {}

    def register(self, model: AIModel) -> None:
        self._models[model.id] = model

    def get(self, model_id: str) -> AIModel | None:
        return self._models.get(model_id)

    def list_all(self) -> list[AIModel]:
        return list(self._models.values())

    def list_by_capability(self, capability: str) -> list[AIModel]:
        return [m for m in self._models.values() if m.supports(capability)]
