from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ExecutionContext:
    job_id: str
    pipeline_id: str
    step_id: str
    capability: str
    action: str
    payload: dict[str, Any]
    model_id: str | None = None
    execution_strategy: str = "auto"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ExecutionResult:
    execution_id: str
    backend: str
    status: ExecutionStatus
    output: dict[str, Any] | None = None
    error: str | None = None
    duration_ms: int | None = None
    completed_at: datetime | None = None

    @property
    def succeeded(self) -> bool:
        return self.status == ExecutionStatus.COMPLETED
