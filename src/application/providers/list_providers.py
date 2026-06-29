from __future__ import annotations

from dataclasses import dataclass

from src.domain.entities.provider import Provider
from src.domain.interfaces.provider_registry import IProviderRegistry


@dataclass
class ListProvidersOutput:
    providers: list[Provider]


class ListProvidersUseCase:
    def __init__(self, provider_registry: IProviderRegistry) -> None:
        self._registry = provider_registry

    async def execute(self) -> ListProvidersOutput:
        providers = [p.get_info() for p in self._registry.list_all()]
        return ListProvidersOutput(providers=providers)
