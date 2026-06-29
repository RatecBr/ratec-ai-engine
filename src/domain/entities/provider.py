from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ProviderType(str, Enum):
    RUNPOD = "runpod"
    COMFYUI = "comfyui"
    OPENAI = "openai"
    LOCAL = "local"


class ProviderStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEGRADED = "degraded"


@dataclass
class Provider:
    id: str
    name: str
    type: ProviderType
    status: ProviderStatus = ProviderStatus.ACTIVE
    capabilities: list[str] | None = None
    metadata: dict | None = None

    def supports(self, capability: str) -> bool:
        if self.capabilities is None:
            return False
        return capability in self.capabilities
