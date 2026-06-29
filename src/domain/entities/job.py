from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    workflow_id: str
    input: dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: JobStatus = JobStatus.PENDING
    output: dict[str, Any] | None = None
    error: str | None = None
    provider_job_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None

    def mark_running(self, provider_job_id: str | None = None) -> None:
        self.status = JobStatus.RUNNING
        self.provider_job_id = provider_job_id
        self.updated_at = datetime.now(timezone.utc)

    def mark_completed(self, output: dict[str, Any]) -> None:
        self.status = JobStatus.COMPLETED
        self.output = output
        self.updated_at = datetime.now(timezone.utc)
        self.completed_at = datetime.now(timezone.utc)

    def mark_failed(self, error: str) -> None:
        self.status = JobStatus.FAILED
        self.error = error
        self.updated_at = datetime.now(timezone.utc)
        self.completed_at = datetime.now(timezone.utc)

    def mark_cancelled(self) -> None:
        self.status = JobStatus.CANCELLED
        self.updated_at = datetime.now(timezone.utc)
        self.completed_at = datetime.now(timezone.utc)

    @property
    def is_terminal(self) -> bool:
        return self.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED)
