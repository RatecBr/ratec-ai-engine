"""
Exemplo de integração — submissão de job e polling de status.

Uso:
    python examples/integration/submit_job.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import httpx

BASE_URL = "http://localhost:8000/v1"


def submit_job(workflow_id: str, input_data: dict) -> dict:
    with httpx.Client() as client:
        r = client.post(f"{BASE_URL}/jobs", json={"workflow_id": workflow_id, "input": input_data})
        r.raise_for_status()
        return r.json()


def get_job(job_id: str) -> dict:
    with httpx.Client() as client:
        r = client.get(f"{BASE_URL}/jobs/{job_id}")
        r.raise_for_status()
        return r.json()


def wait_for_completion(job_id: str, poll_interval: float = 1.0, timeout: float = 60.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        job = get_job(job_id)
        if job["status"] in ("completed", "failed", "cancelled"):
            return job
        time.sleep(poll_interval)
    raise TimeoutError(f"Job '{job_id}' did not complete within {timeout}s")


if __name__ == "__main__":
    payload_path = Path(__file__).parent.parent / "payloads" / "echo.json"
    payload = json.loads(payload_path.read_text())

    print(f"Submetendo job: workflow_id={payload['workflow_id']}")
    job = submit_job(payload["workflow_id"], payload["input"])
    print(f"  Job criado: id={job['id']} status={job['status']}")

    if job["status"] not in ("completed", "failed", "cancelled"):
        print("  Aguardando conclusão...")
        job = wait_for_completion(job["id"])

    print(f"  Status final: {job['status']}")
    if job.get("output"):
        print(f"  Output: {json.dumps(job['output'], indent=2, ensure_ascii=False)}")
    if job.get("error"):
        print(f"  Erro: {job['error']}")
