"""
RATEC AI ENGINE — RunPod Serverless Handler
Sprint 2: Validação de infraestrutura (sem modelos de IA)

Workflows disponíveis:
  echo        — devolve o input exatamente como recebido
  health      — retorna informações do ambiente de execução + GPU
  image-echo  — valida acesso a uma URL de imagem e retorna seus metadados

Input esperado pelo RunPod:
  {
    "input": {
      "workflow_id": "echo" | "health" | "image-echo",
      "input": { ... }
    }
  }
"""
from __future__ import annotations

import os
import platform
import socket
import subprocess
import time
from datetime import datetime, timezone

import httpx
import runpod

VERSION = "1.0.0"
_BOOT_TIME = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Observability — GPU
# ---------------------------------------------------------------------------

def _get_gpu_info() -> dict:
    """
    Coleta informações da GPU via nvidia-smi.
    Retorna dict com métricas de hardware sem referenciar modelos específicos.
    """
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.used,memory.free",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            parts = [p.strip() for p in result.stdout.strip().split(",")]
            return {
                "gpu_model": parts[0] if len(parts) > 0 else None,
                "vram_total_mb": int(parts[1]) if len(parts) > 1 else None,
                "vram_used_mb": int(parts[2]) if len(parts) > 2 else None,
                "vram_free_mb": int(parts[3]) if len(parts) > 3 else None,
            }
    except Exception:
        pass
    return {
        "gpu_model": None,
        "vram_total_mb": None,
        "vram_used_mb": None,
        "vram_free_mb": None,
    }


# Capturado uma vez no boot; raramente muda durante o ciclo de vida do worker.
_GPU_INFO = _get_gpu_info()


# ---------------------------------------------------------------------------
# Workflows
# ---------------------------------------------------------------------------

async def _echo(job_input: dict) -> dict:
    """Devolve exatamente o que recebeu."""
    return job_input


async def _health(job_input: dict) -> dict:
    """Retorna informações do ambiente de execução e do hardware disponível."""
    now = datetime.now(timezone.utc)
    return {
        "version": VERSION,
        "backend": "runpod",
        "environment": os.getenv("ENVIRONMENT", "production"),
        "python_version": platform.python_version(),
        "hostname": socket.gethostname(),
        "worker_ready": True,
        "boot_time": _BOOT_TIME.isoformat(),
        "timestamp": now.isoformat(),
        "uptime_seconds": int((now - _BOOT_TIME).total_seconds()),
        "gpu": _GPU_INFO,
    }


async def _image_echo(job_input: dict) -> dict:
    """Valida acesso a uma URL de imagem e retorna seus metadados."""
    url = job_input.get("url")
    if not url:
        raise ValueError("Campo obrigatório ausente: 'url'")

    t0 = time.monotonic()
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        response = await client.head(url)
        response.raise_for_status()
    latency_ms = int((time.monotonic() - t0) * 1000)

    content_type = response.headers.get("content-type", "")
    if not content_type.startswith("image/"):
        raise ValueError(f"URL não aponta para uma imagem: content-type='{content_type}'")

    return {
        "url": url,
        "accessible": True,
        "content_type": content_type,
        "content_length": response.headers.get("content-length"),
        "status_code": response.status_code,
        "latency_ms": latency_ms,
    }


_WORKFLOWS: dict[str, object] = {
    "echo": _echo,
    "health": _health,
    "image-echo": _image_echo,
}


# ---------------------------------------------------------------------------
# Handler principal
# ---------------------------------------------------------------------------

async def handler(job: dict) -> dict:
    """
    Handler assíncrono nativo para RunPod Serverless SDK >= 1.10.0.
    O SDK detecta `async def` via inspect.iscoroutinefunction() e gerencia
    o event loop internamente. Nunca usar asyncio.run() aqui.
    """
    t_start = time.monotonic()
    job_input: dict = job.get("input", {})

    workflow_id: str | None = job_input.get("workflow_id")
    if not workflow_id:
        return {
            "status": "failed",
            "error": "Campo obrigatório ausente: 'workflow_id'",
        }

    fn = _WORKFLOWS.get(workflow_id)
    if fn is None:
        return {
            "status": "failed",
            "error": f"Workflow desconhecido: '{workflow_id}'. Disponíveis: {list(_WORKFLOWS)}",
        }

    try:
        result = await fn(job_input.get("input", {}))  # type: ignore[operator]
        return {
            "status": "completed",
            "workflow_id": workflow_id,
            "result": result,
            "observability": {
                "execution_time_ms": int((time.monotonic() - t_start) * 1000),
                "gpu_model": _GPU_INFO["gpu_model"],
                "vram_total_mb": _GPU_INFO["vram_total_mb"],
                "vram_used_mb": _GPU_INFO["vram_used_mb"],
            },
        }
    except Exception as exc:
        return {
            "status": "failed",
            "workflow_id": workflow_id,
            "error": str(exc),
            "observability": {
                "execution_time_ms": int((time.monotonic() - t_start) * 1000),
                "gpu_model": _GPU_INFO["gpu_model"],
            },
        }


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

print(f"[ratec] RATEC AI ENGINE v{VERSION} iniciando...", flush=True)
print(f"[ratec] Workflows registrados: {list(_WORKFLOWS)}", flush=True)
print(f"[ratec] Python {platform.python_version()} | Host: {socket.gethostname()}", flush=True)
print(f"[ratec] GPU: {_GPU_INFO.get('gpu_model', 'não detectada')} | "
      f"VRAM: {_GPU_INFO.get('vram_total_mb')} MB", flush=True)

runpod.serverless.start({"handler": handler})
