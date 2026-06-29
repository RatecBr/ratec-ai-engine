import pytest
from src.domain.entities.job import Job, JobStatus
from src.domain.entities.workflow import Workflow, WorkflowStep
from src.infrastructure.providers.local_provider import LocalProvider
from src.infrastructure.providers.provider_registry import ProviderRegistry
from src.infrastructure.workflow_engine.workflow_engine import WorkflowEngine


@pytest.fixture
def engine():
    registry = ProviderRegistry()
    registry.register(LocalProvider())
    wf_engine = WorkflowEngine(registry)
    wf_engine.register_workflow(
        Workflow(
            id="echo",
            name="Echo",
            description="Echo test workflow",
            steps=[
                WorkflowStep(
                    id="step1",
                    provider_type="local",
                    action="echo",
                    parameters={"data": "$input"},
                )
            ],
        )
    )
    return wf_engine


async def test_get_workflow(engine):
    wf = await engine.get_workflow("echo")
    assert wf is not None
    assert wf.id == "echo"


async def test_get_missing_workflow(engine):
    wf = await engine.get_workflow("not-found")
    assert wf is None


async def test_execute_workflow(engine):
    wf = await engine.get_workflow("echo")
    job = Job(workflow_id="echo", input={"hello": "world"})
    result = await engine.execute(job, wf)
    assert result.status == JobStatus.COMPLETED
    assert result.output is not None


async def test_execute_fails_with_unknown_provider(engine):
    wf = Workflow(
        id="broken",
        name="Broken",
        description="Uses a provider that does not exist",
        steps=[WorkflowStep(id="s1", provider_type="nonexistent", action="run", parameters={})],
    )
    job = Job(workflow_id="broken", input={})
    result = await engine.execute(job, wf)
    assert result.status == JobStatus.FAILED
    assert result.error is not None
