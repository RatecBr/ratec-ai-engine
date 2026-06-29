import pytest
from src.domain.entities.job import Job
from src.domain.entities.pipeline import Pipeline, PipelineStep
from src.infrastructure.execution.execution_manager import ExecutionManager
from src.infrastructure.execution.local_backend import LocalBackend
from src.infrastructure.pipeline_engine.pipeline_engine import PipelineEngine


@pytest.fixture
def pipeline_engine():
    manager = ExecutionManager()
    manager.register_backend(LocalBackend())
    return PipelineEngine(manager)


@pytest.fixture
def echo_pipeline():
    return Pipeline(
        id="echo",
        name="Echo",
        description="Echo pipeline",
        steps=[
            PipelineStep(
                id="step1",
                capability="echo",
                action="echo",
                parameters={"data": "$input"},
                execution_strategy="local",
            )
        ],
    )


async def test_execute_pipeline(pipeline_engine, echo_pipeline):
    job = Job(workflow_id="test", input={"msg": "hello"})
    output = await pipeline_engine.execute(job, echo_pipeline, {"msg": "hello"})
    assert isinstance(output, dict)
    assert "action" in output


async def test_execute_pipeline_with_dependency_chain(pipeline_engine):
    pipeline = Pipeline(
        id="chain",
        name="Chain",
        description="Two-step chain",
        steps=[
            PipelineStep(id="step1", capability="echo", action="echo", parameters={"x": "1"}, execution_strategy="local"),
            PipelineStep(id="step2", capability="echo", action="echo", parameters={"x": "2"}, execution_strategy="local", depends_on=["step1"]),
        ],
    )
    job = Job(workflow_id="test", input={})
    output = await pipeline_engine.execute(job, pipeline, {})
    assert isinstance(output, dict)


async def test_execute_fails_with_no_backend():
    manager = ExecutionManager()
    engine = PipelineEngine(manager)
    pipeline = Pipeline(
        id="test",
        name="Test",
        description="Test",
        steps=[PipelineStep(id="s1", capability="anything", action="run", parameters={})],
    )
    job = Job(workflow_id="test", input={})
    with pytest.raises(RuntimeError):
        await engine.execute(job, pipeline, {})


async def test_unresolvable_deps_raises(pipeline_engine):
    pipeline = Pipeline(
        id="broken",
        name="Broken",
        description="Circular deps",
        steps=[
            PipelineStep(id="a", capability="echo", action="echo", parameters={}, execution_strategy="local", depends_on=["b"]),
            PipelineStep(id="b", capability="echo", action="echo", parameters={}, execution_strategy="local", depends_on=["a"]),
        ],
    )
    job = Job(workflow_id="broken", input={})
    with pytest.raises(RuntimeError, match="unresolvable"):
        await pipeline_engine.execute(job, pipeline, {})
