from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.interfaces.provider import IProvider


class IProviderRegistry(ABC):
    @abstractmethod
    def register(self, provider: IProvider) -> None:
        ...

    @abstractmethod
    def get(self, provider_id: str) -> IProvider | None:
        ...

    @abstractmethod
    def get_by_type(self, provider_type: str) -> IProvider | None:
        ...

    @abstractmethod
    def list_all(self) -> list[IProvider]:
        ...
