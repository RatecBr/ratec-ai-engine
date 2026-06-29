from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class UsageRecord:
    """Tracks resource consumption for future billing."""

    job_id: str
    workflow_id: str
    pipeline_id: str
    step_id: str
    capability: str
    model_id: str | None
    backend: str
    app_id: str | None = None
    duration_ms: int | None = None
    units: float | None = None
    unit_type: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
