import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["name"] == "RATEC AI ENGINE"


def test_health():
    r = client.get("/v1/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] in ("ok", "degraded")
    assert "version" in data


def test_list_providers():
    r = client.get("/v1/providers")
    assert r.status_code == 200
    providers = r.json()["providers"]
    assert any(p["id"] == "local" for p in providers)


def test_list_workflows():
    r = client.get("/v1/workflows")
    assert r.status_code == 200
    workflows = r.json()["workflows"]
    assert any(w["id"] == "echo" for w in workflows)


def test_get_workflow():
    r = client.get("/v1/workflows/echo")
    assert r.status_code == 200
    assert r.json()["id"] == "echo"


def test_get_workflow_not_found():
    r = client.get("/v1/workflows/nonexistent")
    assert r.status_code == 404


def test_submit_job_and_get_status():
    r = client.post("/v1/jobs", json={"workflow_id": "echo", "input": {"msg": "hello"}})
    assert r.status_code == 202
    job = r.json()
    job_id = job["id"]
    assert job["workflow_id"] == "echo"

    r2 = client.get(f"/v1/jobs/{job_id}")
    assert r2.status_code == 200
    assert r2.json()["id"] == job_id


def test_submit_job_unknown_workflow():
    r = client.post("/v1/jobs", json={"workflow_id": "unknown", "input": {}})
    assert r.status_code == 404


def test_list_jobs():
    r = client.get("/v1/jobs")
    assert r.status_code == 200
    assert "jobs" in r.json()


def test_cancel_completed_job_fails():
    r = client.post("/v1/jobs", json={"workflow_id": "echo", "input": {}})
    job_id = r.json()["id"]
    r2 = client.post(f"/v1/jobs/{job_id}/cancel")
    assert r2.status_code == 422
