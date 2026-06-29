from __future__ import annotations

from src.domain.entities.provider import Provider
from src.domain.interfaces.provider_registry import IProviderRegistry


class GetProviderUseCase:
    def __init__(self, provider_registry: IProviderRegistry) -> None:
        self._registry = provider_registry

    async def execute(self, provider_id: str) -> Provider:
        provider = self._registry.get(provider_id)
        if provider is None:
            raise ValueError(f"Provider '{provider_id}' not found")
        return provider.get_info()
