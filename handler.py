"""
RunPod Serverless entry point.

Input esperado:
  { "workflow_id": "...", "input": { ... } }
"""
from __future__ import annotations

import asyncio
from typing import Any

import runpod

from src.config.settings import get_settings
from src.domain.entities.job import Job
from src.domain.entities.model import AIModel
from src.domain.entities.pipeline import Pipeline, PipelineStep
from src.domain.entities.workflow import Workflow, WorkflowStep
from src.infrastructure.execution.execution_manager import ExecutionManager
from src.infrastructure.execution.local_backend import LocalBackend
from src.infrastructure.execution.runpod_backend import RunPodBackend
from src.infrastructure.pipeline_engine.pipeline_engine import PipelineEngine
from src.infrastructure.registries.model_registry import ModelRegistry
from src.infrastructure.registries.pipeline_registry import PipelineRegistry
from src.infrastructure.registries.workflow_registry import WorkflowRegistry
from src.infrastructure.workflow_engine.workflow_engine import WorkflowEngine


def _bootstrap() -> tuple[WorkflowEngine, WorkflowRegistry]:
    settings = get_settings()

    execution_manager = ExecutionManager()
    execution_manager.register_backend(LocalBackend())
    if settings.runpod_api_key and settings.runpod_endpoint_id:
        execution_manager.register_backend(RunPodBackend(settings.runpod_api_key, settings.runpod_endpoint_id))

    pipeline_engine = PipelineEngine(execution_manager)

    pipeline_registry = PipelineRegistry()
    pipeline_registry.register(Pipeline(
        id="echo-pipeline",
        name="Echo Pipeline",
        description="Echo pipeline for testing",
        steps=[
            PipelineStep(
                id="echo-step",
                capability="echo",
                action="echo",
                parameters={"data": "$input"},
                execution_strategy="local",
            )
        ],
    ))

    workflow_registry = WorkflowRegistry()
    workflow_registry.register(Workflow(
        id="echo",
        name="Echo Workflow",
        description="Returns input as output",
        steps=[WorkflowStep(id="echo-workflow-step", pipeline_id="echo-pipeline")],
    ))

    engine = WorkflowEngine(pipeline_engine, pipeline_registry)
    return engine, workflow_registry


_engine, _workflow_registry = _bootstrap()


async def _handle_async(job_input: dict[str, Any]) -> dict[str, Any]:
    workflow_id = job_input.get("workflow_id")
    if not workflow_id:
        return {"error": "Missing 'workflow_id' in job input"}

    workflow = _workflow_registry.get(workflow_id)
    if workflow is None:
        return {"error": f"Workflow '{workflow_id}' not found"}

    job = Job(workflow_id=workflow_id, input=job_input.get("input", {}))
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
