from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.domain.entities.job import JobStatus
from src.domain.entities.provider import ProviderStatus, ProviderType


# ── Jobs ─────────────────────────────────────────────────────────────────────

class SubmitJobRequest(BaseModel):
    workflow_id: str
    input: dict[str, Any] = Field(default_factory=dict)


class JobResponse(BaseModel):
    id: str
    workflow_id: str
    status: JobStatus
    input: dict[str, Any]
    output: dict[str, Any] | None = None
    error: str | None = None
    provider_job_id: str | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None


class JobListResponse(BaseModel):
    jobs: list[JobResponse]
    total: int


# ── Workflows ─────────────────────────────────────────────────────────────────

class WorkflowStepResponse(BaseModel):
    id: str
    provider_type: str
    action: str
    parameters: dict[str, Any]
    depends_on: list[str]


class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: str
    version: str
    steps: list[WorkflowStepResponse]
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]


class WorkflowListResponse(BaseModel):
    workflows: list[WorkflowResponse]


# ── Providers ─────────────────────────────────────────────────────────────────

class ProviderResponse(BaseModel):
    id: str
    name: str
    type: ProviderType
    status: ProviderStatus
    capabilities: list[str] | None = None


class ProviderListResponse(BaseModel):
    providers: list[ProviderResponse]


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    providers: dict[str, str]
