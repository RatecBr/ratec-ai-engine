from __future__ import annotations

from typing import Any

from src.domain.entities.job import Job
from src.domain.entities.workflow import Workflow, WorkflowStep
from src.domain.interfaces.provider_registry import IProviderRegistry
from src.domain.interfaces.workflow_engine import IWorkflowEngine


class WorkflowEngine(IWorkflowEngine):
    def __init__(self, provider_registry: IProviderRegistry) -> None:
        self._registry = provider_registry
        self._workflows: dict[str, Workflow] = {}

    def register_workflow(self, workflow: Workflow) -> None:
        self._workflows[workflow.id] = workflow

    async def get_workflow(self, workflow_id: str) -> Workflow | None:
        return self._workflows.get(workflow_id)

    async def list_workflows(self) -> list[Workflow]:
        return list(self._workflows.values())

    async def execute(self, job: Job, workflow: Workflow) -> Job:
        try:
            job.mark_running()
            context: dict[str, Any] = {"input": job.input}

            completed: set[str] = set()
            pending = list(workflow.steps)

            while pending:
                ready = [s for s in pending if all(dep in completed for dep in s.depends_on)]
                if not ready:
                    raise RuntimeError("Workflow has unresolvable step dependencies")

                for step in ready:
                    step_output = await self._execute_step(step, context)
                    context[step.id] = step_output
                    completed.add(step.id)
                    pending.remove(step)

            last_step_id = workflow.steps[-1].id
            job.mark_completed(output=context.get(last_step_id, {}))

        except Exception as exc:
            job.mark_failed(error=str(exc))

        return job

    async def _execute_step(self, step: WorkflowStep, context: dict[str, Any]) -> dict[str, Any]:
        provider = self._registry.get_by_type(step.provider_type)
        if provider is None:
            raise RuntimeError(f"No provider available for type '{step.provider_type}'")

        resolved_params = self._resolve_params(step.parameters, context)
        result = await provider.run(step.action, resolved_params)
        return result

    def _resolve_params(self, params: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        resolved: dict[str, Any] = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("$"):
                parts = value[1:].split(".", 1)
                source = context.get(parts[0], {})
                resolved[key] = source.get(parts[1]) if len(parts) > 1 and isinstance(source, dict) else source
            else:
                resolved[key] = value
        return resolved
