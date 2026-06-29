from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.domain.entities.job import JobStatus
from src.domain.entities.model import ModelStatus
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
    pipeline_id: str
    input_mapping: dict[str, str]
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


# ── Pipelines ─────────────────────────────────────────────────────────────────

class PipelineStepResponse(BaseModel):
    id: str
    capability: str
    action: str
    parameters: dict[str, Any]
    model_id: str | None = None
    execution_strategy: str
    depends_on: list[str]


class PipelineResponse(BaseModel):
    id: str
    name: str
    description: str
    version: str
    steps: list[PipelineStepResponse]
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]


class PipelineListResponse(BaseModel):
    pipelines: list[PipelineResponse]


# ── Models ────────────────────────────────────────────────────────────────────

class ModelResponse(BaseModel):
    id: str
    name: str
    provider_type: str
    capabilities: list[str]
    status: ModelStatus
    version: str
    requirements: dict[str, Any]


class ModelListResponse(BaseModel):
    models: list[ModelResponse]


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
    backends: dict[str, str]
