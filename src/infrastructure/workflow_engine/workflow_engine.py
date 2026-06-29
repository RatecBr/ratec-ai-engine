from __future__ import annotations

from typing import Any

from src.domain.entities.job import Job
from src.domain.entities.workflow import Workflow, WorkflowStep
from src.domain.interfaces.pipeline_engine import IPipelineEngine
from src.domain.interfaces.pipeline_registry import IPipelineRegistry
from src.domain.interfaces.workflow_engine import IWorkflowEngine


class WorkflowEngine(IWorkflowEngine):
    """
    Executa Workflows delegando cada step ao PipelineEngine.
    Não conhece providers, modelos ou backends de execução.
    """

    def __init__(self, pipeline_engine: IPipelineEngine, pipeline_registry: IPipelineRegistry) -> None:
        self._pipeline_engine = pipeline_engine
        self._pipeline_registry = pipeline_registry

    async def execute(self, job: Job, workflow: Workflow) -> Job:
        try:
            job.mark_running()
            context: dict[str, Any] = {"input": job.input}

            completed: set[str] = set()
            pending = list(workflow.steps)

            while pending:
                ready = [s for s in pending if all(dep in completed for dep in s.depends_on)]
                if not ready:
                    raise RuntimeError(f"Workflow '{workflow.id}' has unresolvable step dependencies")

                for step in ready:
                    step_output = await self._execute_step(job, step, context)
                    context[step.id] = step_output
                    completed.add(step.id)
                    pending.remove(step)

            last_step_id = workflow.steps[-1].id
            job.mark_completed(output=context.get(last_step_id, {}))

        except Exception as exc:
            job.mark_failed(error=str(exc))

        return job

    async def _execute_step(
        self, job: Job, step: WorkflowStep, context: dict[str, Any]
    ) -> dict[str, Any]:
        pipeline = self._pipeline_registry.get(step.pipeline_id)
        if pipeline is None:
            raise RuntimeError(f"Pipeline '{step.pipeline_id}' not found in registry")

        input_data = self._resolve_input(step.input_mapping, context)
        return await self._pipeline_engine.execute(job, pipeline, input_data)

    def _resolve_input(self, mapping: dict[str, str], context: dict[str, Any]) -> dict[str, Any]:
        if not mapping:
            return context.get("input", {})
        resolved: dict[str, Any] = {}
        for target_key, source_path in mapping.items():
            parts = source_path.lstrip("$").split(".", 1)
            source = context.get(parts[0], {})
            resolved[target_key] = source.get(parts[1]) if len(parts) > 1 and isinstance(source, dict) else source
        return resolved
