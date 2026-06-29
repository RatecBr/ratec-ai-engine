import pytest
from src.domain.entities.job import Job, JobStatus
from src.domain.entities.pipeline import Pipeline, PipelineStep
from src.domain.entities.workflow import Workflow, WorkflowStep
from src.infrastructure.execution.execution_manager import ExecutionManager
from src.infrastructure.execution.local_backend import LocalBackend
from src.infrastructure.pipeline_engine.pipeline_engine import PipelineEngine
from src.infrastructure.registries.pipeline_registry import PipelineRegistry
from src.infrastructure.workflow_engine.workflow_engine import WorkflowEngine


@pytest.fixture
def pipeline_registry():
    registry = PipelineRegistry()
    registry.register(Pipeline(
        id="echo-pipeline",
        name="Echo",
        description="Echo test",
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
    return registry


@pytest.fixture
def workflow_engine(pipeline_registry):
    execution_manager = ExecutionManager()
    execution_manager.register_backend(LocalBackend())
    pipeline_engine = PipelineEngine(execution_manager)
    return WorkflowEngine(pipeline_engine, pipeline_registry)


async def test_execute_workflow(workflow_engine):
    workflow = Workflow(
        id="test-wf",
        name="Test",
        description="Test workflow",
        steps=[WorkflowStep(id="s1", pipeline_id="echo-pipeline")],
    )
    job = Job(workflow_id="test-wf", input={"hello": "world"})
    result = await workflow_engine.execute(job, workflow)
    assert result.status == JobStatus.COMPLETED
    assert result.output is not None


async def test_execute_fails_with_unknown_pipeline(workflow_engine):
    workflow = Workflow(
        id="broken",
        name="Broken",
        description="Uses pipeline that does not exist",
        steps=[WorkflowStep(id="s1", pipeline_id="nonexistent-pipeline")],
    )
    job = Job(workflow_id="broken", input={})
    result = await workflow_engine.execute(job, workflow)
    assert result.status == JobStatus.FAILED
    assert result.error is not None
