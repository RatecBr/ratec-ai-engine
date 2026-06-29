from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ComfyUIPromptResponse:
    prompt_id: str
    number: int
    node_errors: dict[str, Any] = field(default_factory=dict)


@dataclass
class ComfyUIOutputImage:
    filename: str
    subfolder: str
    type: str  # "output" | "temp"
    node_id: str


@dataclass
class ComfyUIJobResult:
    prompt_id: str
    outputs: dict[str, Any]
    images: list[ComfyUIOutputImage]
    elapsed_ms: int
