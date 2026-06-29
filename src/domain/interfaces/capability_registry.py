from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.capability import Capability
from src.domain.entities.model import AIModel


class ICapabilityRegistry(ABC):
    """
    Mapeia capabilities abstratas para os modelos que as suportam.

    Permite que Workflows solicitem "image-generation" sem conhecer
    se será FLUX.1, SDXL ou qualquer outro modelo.
    O registry resolve o melhor modelo disponível para a capability.
    """

    @abstractmethod
    def register_capability(self, capability: Capability) -> None:
        ...

    @abstractmethod
    def get_capability(self, capability_id: str) -> Capability | None:
        ...

    @abstractmethod
    def list_capabilities(self) -> list[Capability]:
        ...

    @abstractmethod
    def resolve_model(self, capability_id: str) -> AIModel | None:
        """Retorna o melhor modelo disponível para a capability."""
        ...

    @abstractmethod
    def list_models_for_capability(self, capability_id: str) -> list[AIModel]:
        """Retorna todos os modelos que suportam a capability, em ordem de preferência."""
        ...
