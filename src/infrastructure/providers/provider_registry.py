from __future__ import annotations

from src.domain.interfaces.provider import IProvider
from src.domain.interfaces.provider_registry import IProviderRegistry


class ProviderRegistry(IProviderRegistry):
    def __init__(self) -> None:
        self._providers: dict[str, IProvider] = {}

    def register(self, provider: IProvider) -> None:
        info = provider.get_info()
        self._providers[info.id] = provider

    def get(self, provider_id: str) -> IProvider | None:
        return self._providers.get(provider_id)

    def get_by_type(self, provider_type: str) -> IProvider | None:
        return next(
            (p for p in self._providers.values() if p.get_info().type.value == provider_type),
            None,
        )

    def list_all(self) -> list[IProvider]:
        return list(self._providers.values())
