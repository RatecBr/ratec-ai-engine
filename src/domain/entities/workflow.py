from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class WorkflowStep:
    id: str
    provider_type: str
    action: str
    parameters: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)


@dataclass
class Workflow:
    id: str
    name: str
    description: str
    steps: list[WorkflowStep]
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"

    def get_step(self, step_id: str) -> WorkflowStep | None:
        return next((s for s in self.steps if s.id == step_id), None)

    def get_entry_steps(self) -> list[WorkflowStep]:
        return [s for s in self.steps if not s.depends_on]
