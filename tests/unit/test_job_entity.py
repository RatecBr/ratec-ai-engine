import pytest
from src.domain.entities.job import Job, JobStatus


def test_job_initial_status():
    job = Job(workflow_id="echo", input={"key": "value"})
    assert job.status == JobStatus.PENDING
    assert not job.is_terminal


def test_job_mark_running():
    job = Job(workflow_id="echo", input={})
    job.mark_running(provider_job_id="prov-123")
    assert job.status == JobStatus.RUNNING
    assert job.provider_job_id == "prov-123"


def test_job_mark_completed():
    job = Job(workflow_id="echo", input={})
    job.mark_completed(output={"result": "ok"})
    assert job.status == JobStatus.COMPLETED
    assert job.output == {"result": "ok"}
    assert job.is_terminal


def test_job_mark_failed():
    job = Job(workflow_id="echo", input={})
    job.mark_failed(error="something went wrong")
    assert job.status == JobStatus.FAILED
    assert job.error == "something went wrong"
    assert job.is_terminal


def test_job_mark_cancelled():
    job = Job(workflow_id="echo", input={})
    job.mark_cancelled()
    assert job.status == JobStatus.CANCELLED
    assert job.is_terminal
