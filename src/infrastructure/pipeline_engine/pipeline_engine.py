from __future__ import annotations

from typing import Any

from src.domain.entities.execution import ExecutionContext
from src.domain.entities.job import Job
from src.domain.entities.pipeline import Pipeline, PipelineStep
from src.domain.interfaces.execution_manager import IExecutionManager
from src.domain.interfaces.pipeline_engine import IPipelineEngine


class PipelineEngine(IPipelineEngine):
    """
    Executa um Pipeline resolvendo cada step via ExecutionManager.
    Não conhece providers específicos, modelos concretos ou backends de execução.
    """

    def __init__(self, execution_manager: IExecutionManager) -> None:
        self._execution_manager = execution_manager

    async def execute(self, job: Job, pipeline: Pipeline, input_data: dict[str, Any]) -> dict[str, Any]:
        context: dict[str, Any] = {"input": input_data}
        completed: set[str] = set()
        pending = list(pipeline.steps)

        while pending:
            ready = [s for s in pending if all(dep in completed for dep in s.depends_on)]
            if not ready:
                raise RuntimeError(f"Pipeline '{pipeline.id}' has unresolvable step dependencies")

            for step in ready:
                step_output = await self._execute_step(job, pipeline, step, context)
                context[step.id] = step_output
                completed.add(step.id)
                pending.remove(step)

        last_step_id = pipeline.steps[-1].id
        return context.get(last_step_id, {})

    async def _execute_step(
        self,
        job: Job,
        pipeline: Pipeline,
        step: PipelineStep,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        resolved_params = self._resolve_params(step.parameters, context)

        exec_context = ExecutionContext(
            job_id=job.id,
            pipeline_id=pipeline.id,
            step_id=step.id,
            capability=step.capability,
            action=step.action,
            payload=resolved_params,
            model_id=step.model_id,
            execution_strategy=step.execution_strategy,
        )

        result = await self._execution_manager.execute(exec_context)

        if not result.succeeded:
            raise RuntimeError(f"Step '{step.id}' failed: {result.error}")

        return result.output or {}

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
