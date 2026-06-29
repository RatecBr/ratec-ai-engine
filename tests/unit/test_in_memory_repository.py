import pytest
from src.domain.entities.job import Job, JobStatus
from src.infrastructure.repositories.in_memory_job_repository import InMemoryJobRepository


@pytest.fixture
def repo():
    return InMemoryJobRepository()


async def test_save_and_get(repo):
    job = Job(workflow_id="echo", input={"x": 1})
    await repo.save(job)
    found = await repo.get_by_id(job.id)
    assert found is not None
    assert found.id == job.id


async def test_get_missing(repo):
    result = await repo.get_by_id("nonexistent")
    assert result is None


async def test_list_all(repo):
    j1 = Job(workflow_id="echo", input={})
    j2 = Job(workflow_id="echo", input={})
    await repo.save(j1)
    await repo.save(j2)
    jobs = await repo.list()
    assert len(jobs) == 2


async def test_list_filter_by_status(repo):
    j1 = Job(workflow_id="echo", input={})
    j2 = Job(workflow_id="echo", input={})
    j2.mark_completed(output={})
    await repo.save(j1)
    await repo.save(j2)
    pending = await repo.list(status=JobStatus.PENDING)
    assert len(pending) == 1
    assert pending[0].id == j1.id


async def test_delete(repo):
    job = Job(workflow_id="echo", input={})
    await repo.save(job)
    deleted = await repo.delete(job.id)
    assert deleted is True
    assert await repo.get_by_id(job.id) is None
