"""
RunPod Serverless entry point.

Receives jobs from RunPod and dispatches them through the WorkflowEngine.
Each RunPod job must provide:
  {
    "workflow_id": "...",
    "input": { ... }
  }
"""
from __future__ import annotations

import asyncio
import os
from typing import Any

import runpod

from src.config.settings import get_settings
from src.domain.entities.workflow import Workflow, WorkflowStep
from src.infrastructure.providers.local_provider import LocalProvider
from src.infrastructure.providers.provider_registry import ProviderRegistry
from src.infrastructure.providers.runpod_provider import RunPodProvider
from src.infrastructure.workflow_engine.workflow_engine import WorkflowEngine


def _build_engine() -> WorkflowEngine:
    settings = get_settings()
    registry = ProviderRegistry()
    registry.register(LocalProvider())

    if settings.runpod_api_key and settings.runpod_endpoint_id:
        registry.register(RunPodProvider(settings.runpod_api_key, settings.runpod_endpoint_id))

    engine = WorkflowEngine(registry)

    echo_workflow = Workflow(
        id="echo",
        name="Echo Workflow",
        description="Returns the input as-is.",
        steps=[
            WorkflowStep(
                id="echo_step",
                provider_type="local",
                action="echo",
                parameters={"data": "$input"},
            )
        ],
    )
    engine.register_workflow(echo_workflow)
    return engine


_engine = _build_engine()


async def _handle_async(job_input: dict[str, Any]) -> dict[str, Any]:
    workflow_id = job_input.get("workflow_id")
    if not workflow_id:
        return {"error": "Missing 'workflow_id' in job input"}

    payload = job_input.get("input", {})
    workflow = await _engine.get_workflow(workflow_id)
    if workflow is None:
        return {"error": f"Workflow '{workflow_id}' not found"}

    from src.domain.entities.job import Job

    job = Job(workflow_id=workflow_id, input=payload)
    job = await _engine.execute(job, workflow)

    return {
        "job_id": job.id,
        "status": job.status.value,
        "output": job.output,
        "error": job.error,
    }


def handler(job: dict[str, Any]) -> dict[str, Any]:
    return asyncio.run(_handle_async(job.get("input", {})))


if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
