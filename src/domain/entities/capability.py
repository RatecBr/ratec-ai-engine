from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Capability:
    """
    Representa uma capacidade abstrata de IA oferecida pela plataforma.

    Workflows e Pipelines solicitam Capabilities em vez de modelos específicos.
    O CapabilityRegistry resolve qual modelo e provider atende à capability
    em runtime, garantindo desacoplamento total do workflow da tecnologia.

    Exemplos: "image-generation", "text-generation", "audio-transcription",
              "image-upscale", "face-swap", "video-generation"
    """

    id: str
    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def tags(self) -> list[str]:
        return self.metadata.get("tags", [])
