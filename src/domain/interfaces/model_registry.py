from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.model import AIModel


class IModelRegistry(ABC):
    @abstractmethod
    def register(self, model: AIModel) -> None:
        ...

    @abstractmethod
    def get(self, model_id: str) -> AIModel | None:
        ...

    @abstractmethod
    def list_all(self) -> list[AIModel]:
        ...

    @abstractmethod
    def list_by_capability(self, capability: str) -> list[AIModel]:
        ...
