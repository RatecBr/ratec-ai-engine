from __future__ import annotations

from functools import lru_cache

from fastapi import Depends

from src.application.jobs.cancel_job import CancelJobUseCase
from src.application.jobs.get_job_status import GetJobStatusUseCase
from src.application.jobs.list_jobs import ListJobsUseCase
from src.application.jobs.submit_job import SubmitJobUseCase
from src.application.models.get_model import GetModelUseCase
from src.application.models.list_models import ListModelsUseCase
from src.application.pipelines.execute_pipeline import ExecutePipelineUseCase
from src.application.pipelines.get_pipeline import GetPipelineUseCase
from src.application.pipelines.list_pipelines import ListPipelinesUseCase
from src.application.providers.get_provider import GetProviderUseCase
from src.application.providers.list_providers import ListProvidersUseCase
from src.application.workflows.get_workflow import GetWorkflowUseCase
from src.application.workflows.list_workflows import ListWorkflowsUseCase
from src.config.settings import get_settings
from src.domain.entities.model import AIModel
from src.domain.entities.pipeline import Pipeline, PipelineStep
from src.domain.entities.workflow import Workflow, WorkflowStep
from src.domain.interfaces.job_repository import IJobRepository
from src.domain.interfaces.model_registry import IModelRegistry
from src.domain.interfaces.pipeline_engine import IPipelineEngine
from src.domain.interfaces.pipeline_registry import IPipelineRegistry
from src.domain.interfaces.provider_registry import IProviderRegistry
from src.domain.interfaces.workflow_engine import IWorkflowEngine
from src.domain.interfaces.workflow_registry import IWorkflowRegistry
from src.infrastructure.execution.execution_manager import ExecutionManager
from src.infrastructure.execution.local_backend import LocalBackend
from src.infrastructure.execution.runpod_backend import RunPodBackend
from src.infrastructure.pipeline_engine.pipeline_engine import PipelineEngine
from src.infrastructure.providers.local_provider import LocalProvider
from src.infrastructure.providers.provider_registry import ProviderRegistry
from src.infrastructure.providers.runpod_provider import RunPodProvider
from src.infrastructure.registries.model_registry import ModelRegistry
from src.infrastructure.registries.pipeline_registry import PipelineRegistry as InfraPipelineRegistry
from src.infrastructure.registries.workflow_registry import WorkflowRegistry
from src.infrastructure.repositories.in_memory_job_repository import InMemoryJobRepository
from src.infrastructure.workflow_engine.workflow_engine import WorkflowEngine


# ── Execution Manager ─────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _build_execution_manager() -> ExecutionManager:
    settings = get_settings()
    manager = ExecutionManager()
    manager.register_backend(LocalBackend())
    if settings.runpod_api_key and settings.runpod_endpoint_id:
        manager.register_backend(RunPodBackend(settings.runpod_api_key, settings.runpod_endpoint_id))
    return manager


# ── Model Registry ────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _build_model_registry() -> ModelRegistry:
    registry = ModelRegistry()
    registry.register(AIModel(
        id="local-echo",
        name="Local Echo (Dev)",
        provider_type="local",
        capabilities=["echo", "mock"],
    ))
    # Futuros modelos são registrados aqui sem impacto nos workflows/pipelines:
    # registry.register(AIModel(id="flux-1-dev", name="FLUX.1 Dev", provider_type="image-generation",
    #     capabilities=["image-generation", "inpainting"], requirements={"gpu_memory": "24GB"}))
    # registry.register(AIModel(id="gpt-4o", name="GPT-4o", provider_type="text-generation",
    #     capabilities=["text-generation", "chat"]))
    return registry


# ── Pipeline Registry ─────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _build_pipeline_registry() -> InfraPipelineRegistry:
    registry = InfraPipelineRegistry()
    registry.register(Pipeline(
        id="echo-pipeline",
        name="Echo Pipeline",
        description="Ecoa o input de volta. Pipeline de desenvolvimento e teste.",
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
    # Futuros pipelines são registrados aqui:
    # registry.register(Pipeline(id="image-generation-pipeline", ...))
    # registry.register(Pipeline(id="video-generation-pipeline", ...))
    return registry


# ── Workflow Registry ─────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _build_workflow_registry() -> WorkflowRegistry:
    registry = WorkflowRegistry()
    registry.register(Workflow(
        id="echo",
        name="Echo Workflow",
        description="Retorna o input como output. Útil para testes de integração.",
        steps=[
            WorkflowStep(
                id="echo-workflow-step",
                pipeline_id="echo-pipeline",
            )
        ],
    ))
    # Futuros workflows são registrados aqui sem conhecer providers ou modelos:
    # registry.register(Workflow(id="generate-profile-photo", steps=[
    #     WorkflowStep(id="step1", pipeline_id="image-generation-pipeline"),
    # ]))
    return registry


# ── Provider Registry (para /v1/providers) ────────────────────────────────────

@lru_cache(maxsize=1)
def _build_provider_registry() -> ProviderRegistry:
    settings = get_settings()
    registry = ProviderRegistry()
    registry.register(LocalProvider())
    if settings.runpod_api_key and settings.runpod_endpoint_id:
        registry.register(RunPodProvider(settings.runpod_api_key, settings.runpod_endpoint_id))
    return registry


# ── Core engines ──────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _build_job_repository() -> InMemoryJobRepository:
    return InMemoryJobRepository()


@lru_cache(maxsize=1)
def _build_pipeline_engine(execution_manager: ExecutionManager) -> PipelineEngine:
    return PipelineEngine(execution_manager)


@lru_cache(maxsize=1)
def _build_workflow_engine(
    pipeline_engine: PipelineEngine,
    pipeline_registry: InfraPipelineRegistry,
) -> WorkflowEngine:
    return WorkflowEngine(pipeline_engine, pipeline_registry)


# ── FastAPI dependency functions ──────────────────────────────────────────────

def get_execution_manager() -> ExecutionManager:
    return _build_execution_manager()


def get_model_registry() -> IModelRegistry:
    return _build_model_registry()


def get_pipeline_registry() -> IPipelineRegistry:
    return _build_pipeline_registry()


def get_workflow_registry() -> IWorkflowRegistry:
    return _build_workflow_registry()


def get_provider_registry() -> IProviderRegistry:
    return _build_provider_registry()


def get_job_repository() -> IJobRepository:
    return _build_job_repository()


def get_pipeline_engine() -> IPipelineEngine:
    return _build_pipeline_engine(_build_execution_manager())


def get_workflow_engine() -> IWorkflowEngine:
    return _build_workflow_engine(_build_pipeline_engine(_build_execution_manager()), _build_pipeline_registry())


# Jobs
def get_submit_job_uc(
    repo: IJobRepository = Depends(get_job_repository),
    engine: IWorkflowEngine = Depends(get_workflow_engine),
    workflow_registry: IWorkflowRegistry = Depends(get_workflow_registry),
) -> SubmitJobUseCase:
    return SubmitJobUseCase(repo, engine, workflow_registry)


def get_get_job_status_uc(repo: IJobRepository = Depends(get_job_repository)) -> GetJobStatusUseCase:
    return GetJobStatusUseCase(repo)


def get_cancel_job_uc(repo: IJobRepository = Depends(get_job_repository)) -> CancelJobUseCase:
    return CancelJobUseCase(repo)


def get_list_jobs_uc(repo: IJobRepository = Depends(get_job_repository)) -> ListJobsUseCase:
    return ListJobsUseCase(repo)


# Workflows
def get_list_workflows_uc(registry: IWorkflowRegistry = Depends(get_workflow_registry)) -> ListWorkflowsUseCase:
    return ListWorkflowsUseCase(registry)


def get_get_workflow_uc(registry: IWorkflowRegistry = Depends(get_workflow_registry)) -> GetWorkflowUseCase:
    return GetWorkflowUseCase(registry)


# Pipelines
def get_list_pipelines_uc(registry: IPipelineRegistry = Depends(get_pipeline_registry)) -> ListPipelinesUseCase:
    return ListPipelinesUseCase(registry)


def get_get_pipeline_uc(registry: IPipelineRegistry = Depends(get_pipeline_registry)) -> GetPipelineUseCase:
    return GetPipelineUseCase(registry)


def get_execute_pipeline_uc() -> ExecutePipelineUseCase:
    return ExecutePipelineUseCase(get_pipeline_engine(), get_pipeline_registry())


# Models
def get_list_models_uc(registry: IModelRegistry = Depends(get_model_registry)) -> ListModelsUseCase:
    return ListModelsUseCase(registry)


def get_get_model_uc(registry: IModelRegistry = Depends(get_model_registry)) -> GetModelUseCase:
    return GetModelUseCase(registry)


# Providers
def get_list_providers_uc(registry: IProviderRegistry = Depends(get_provider_registry)) -> ListProvidersUseCase:
    return ListProvidersUseCase(registry)


def get_get_provider_uc(registry: IProviderRegistry = Depends(get_provider_registry)) -> GetProviderUseCase:
    return GetProviderUseCase(registry)
