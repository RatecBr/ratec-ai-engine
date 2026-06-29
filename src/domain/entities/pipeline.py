from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PipelineStep:
    id: str
    capability: str
    action: str
    parameters: dict[str, Any] = field(default_factory=dict)
    model_id: str | None = None
    execution_strategy: str = "auto"
    depends_on: list[str] = field(default_factory=list)


@dataclass
class Pipeline:
    id: str
    name: str
    description: str
    steps: list[PipelineStep]
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"

    def get_step(self, step_id: str) -> PipelineStep | None:
        return next((s for s in self.steps if s.id == step_id), None)

    def get_entry_steps(self) -> list[PipelineStep]:
        return [s for s in self.steps if not s.depends_on]
