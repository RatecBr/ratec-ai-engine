from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ManifestRequirements:
    gpu: bool = False
    min_vram: str | None = None
    min_memory: str | None = None
    cuda_version: str | None = None


@dataclass
class WorkflowManifest:
    """
    Metadados declarativos de um Workflow.

    O manifesto descreve O QUE um workflow precisa (capabilities, requisitos,
    modelo preferencial) sem conhecer COMO ou ONDE será executado.
    Serve como contrato de registro e documentação do workflow.
    """

    id: str
    version: str
    name: str
    description: str
    pipeline: str
    capabilities: list[str]
    requirements: ManifestRequirements = field(default_factory=ManifestRequirements)
    model: str | None = None
    provider: str | None = None
    capability: str | None = None
    estimated_time_seconds: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def requires_gpu(self) -> bool:
        return self.requirements.gpu

    @property
    def is_stable(self) -> bool:
        return self.metadata.get("stable", False)

    @property
    def tags(self) -> list[str]:
        return self.metadata.get("tags", [])
