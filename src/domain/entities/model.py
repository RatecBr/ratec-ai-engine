from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ModelStatus(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEPRECATED = "deprecated"


@dataclass
class AIModel:
    id: str
    name: str
    provider_type: str
    capabilities: list[str]
    status: ModelStatus = ModelStatus.AVAILABLE
    version: str = "1.0.0"
    requirements: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def supports(self, capability: str) -> bool:
        return capability in self.capabilities
