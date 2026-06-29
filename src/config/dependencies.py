from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from src.application.jobs.cancel_job import CancelJobUseCase
from src.application.jobs.get_job_status import GetJobStatusUseCase
from src.application.jobs.list_jobs import ListJobsUseCase
from src.application.jobs.submit_job import SubmitJobUseCase
from src.application.providers.get_provider import GetProviderUseCase
from src.application.providers.list_providers import ListProvidersUseCase
from src.application.workflows.get_workflow import GetWorkflowUseCase
from src.application.workflows.list_workflows import ListWorkflowsUseCase
from src.config.settings import Settings, get_settings
from src.domain.interfaces.job_repository import IJobRepository
from src.domain.interfaces.provider_registry import IProviderRegistry
from src.domain.interfaces.workflow_engine import IWorkflowEngine
from src.infrastructure.providers.local_provider import LocalProvider
from src.infrastructure.providers.provider_registry import ProviderRegistry
from src.infrastructure.providers.runpod_provider import RunPodProvider
from src.infrastructure.repositories.in_memory_job_repository import InMemoryJobRepository
from src.infrastructure.workflow_engine.workflow_engine import WorkflowEngine


# ── Singletons ────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _build_provider_registry(settings: Settings) -> ProviderRegistry:
    registry = ProviderRegistry()
    registry.register(LocalProvider())
    if settings.runpod_api_key and settings.runpod_endpoint_id:
        registry.register(RunPodProvider(settings.runpod_api_key, settings.runpod_endpoint_id))
    return registry


@lru_cache(maxsize=1)
def _build_job_repository() -> InMemoryJobRepository:
    return InMemoryJobRepository()


@lru_cache(maxsize=1)
def _build_workflow_engine(registry: ProviderRegistry) -> WorkflowEngine:
    engine = WorkflowEngine(registry)
    _register_default_workflows(engine)
    return engine


def _register_default_workflows(engine: WorkflowEngine) -> None:
    from src.domain.entities.workflow import Workflow, WorkflowStep

    echo_workflow = Workflow(
        id="echo",
        name="Echo Workflow",
        description="Returns the input as-is. Useful for testing.",
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


# ── FastAPI dependency functions ──────────────────────────────────────────────

def get_provider_registry(settings: Settings = Depends(get_settings)) -> IProviderRegistry:
    return _build_provider_registry(settings)


def get_job_repository() -> IJobRepository:
    return _build_job_repository()


def get_workflow_engine(registry: IProviderRegistry = Depends(get_provider_registry)) -> IWorkflowEngine:
    return _build_workflow_engine(registry)  # type: ignore[arg-type]


def get_submit_job_uc(
    repo: IJobRepository = Depends(get_job_repository),
    engine: IWorkflowEngine = Depends(get_workflow_engine),
) -> SubmitJobUseCase:
    return SubmitJobUseCase(repo, engine)


def get_get_job_status_uc(repo: IJobRepository = Depends(get_job_repository)) -> GetJobStatusUseCase:
    return GetJobStatusUseCase(repo)


def get_cancel_job_uc(repo: IJobRepository = Depends(get_job_repository)) -> CancelJobUseCase:
    return CancelJobUseCase(repo)


def get_list_jobs_uc(repo: IJobRepository = Depends(get_job_repository)) -> ListJobsUseCase:
    return ListJobsUseCase(repo)


def get_list_workflows_uc(engine: IWorkflowEngine = Depends(get_workflow_engine)) -> ListWorkflowsUseCase:
    return ListWorkflowsUseCase(engine)


def get_get_workflow_uc(engine: IWorkflowEngine = Depends(get_workflow_engine)) -> GetWorkflowUseCase:
    return GetWorkflowUseCase(engine)


def get_list_providers_uc(registry: IProviderRegistry = Depends(get_provider_registry)) -> ListProvidersUseCase:
    return ListProvidersUseCase(registry)


def get_get_provider_uc(registry: IProviderRegistry = Depends(get_provider_registry)) -> GetProviderUseCase:
    return GetProviderUseCase(registry)
