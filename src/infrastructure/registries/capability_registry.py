from __future__ import annotations

from src.domain.entities.capability import Capability
from src.domain.entities.model import AIModel, ModelStatus
from src.domain.interfaces.capability_registry import ICapabilityRegistry
from src.domain.interfaces.model_registry import IModelRegistry


class CapabilityRegistry(ICapabilityRegistry):
    """
    Mantém o catálogo de capabilities e resolve qual modelo usar para cada uma.

    A resolução segue esta ordem de prioridade:
    1. Modelos explicitamente preferidos via set_preferred_model()
    2. Primeiro modelo disponível (status=AVAILABLE) que suporte a capability

    Isso garante que workflows nunca precisam ser alterados quando um novo
    modelo melhor se torna disponível — basta atualizar a preferência aqui.
    """

    def __init__(self, model_registry: IModelRegistry) -> None:
        self._capabilities: dict[str, Capability] = {}
        self._preferred_models: dict[str, str] = {}
        self._model_registry = model_registry

    def register_capability(self, capability: Capability) -> None:
        self._capabilities[capability.id] = capability

    def get_capability(self, capability_id: str) -> Capability | None:
        return self._capabilities.get(capability_id)

    def list_capabilities(self) -> list[Capability]:
        return list(self._capabilities.values())

    def set_preferred_model(self, capability_id: str, model_id: str) -> None:
        """Define o modelo preferencial para uma capability."""
        self._preferred_models[capability_id] = model_id

    def resolve_model(self, capability_id: str) -> AIModel | None:
        preferred_id = self._preferred_models.get(capability_id)
        if preferred_id:
            model = self._model_registry.get(preferred_id)
            if model and model.status == ModelStatus.AVAILABLE:
                return model

        available = self.list_models_for_capability(capability_id)
        return available[0] if available else None

    def list_models_for_capability(self, capability_id: str) -> list[AIModel]:
        return [
            m for m in self._model_registry.list_by_capability(capability_id)
            if m.status == ModelStatus.AVAILABLE
        ]
