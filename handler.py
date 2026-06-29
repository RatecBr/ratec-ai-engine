"""
RATEC AI ENGINE — RunPod Serverless Handler

Workflows disponíveis:
  echo              — devolve o input exatamente como recebido
  health            — retorna informações do ambiente de execução + GPU + ComfyUI
  image-echo        — valida acesso a uma URL de imagem e retorna seus metadados
  image-identity    — carrega uma imagem no ComfyUI e a retorna sem modificação

Input esperado pelo RunPod:
  {
    "input": {
      "workflow_id": "echo" | "health" | "image-echo" | "image-identity",
      "input": { ... }
    }
  }
"""
from __future__ import annotations

import asyncio
import base64
import json
import os
import platform
import socket
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx
import runpod

VERSION = "1.1.0"
_BOOT_TIME = datetime.now(timezone.utc)
_CLIENT_ID = str(uuid.uuid4())
_COMFYUI_URL = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")
_WORKFLOWS_DIR = Path(__file__).parent / "workflows"


# ---------------------------------------------------------------------------
# Observability — GPU
# ---------------------------------------------------------------------------

def _get_gpu_info() -> dict:
    """Coleta informações da GPU via nvidia-smi sem referenciar modelos específicos."""
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


_GPU_INFO = _get_gpu_info()


# ---------------------------------------------------------------------------
# ComfyUI — cliente mínimo (self-contained, sem imports de src/)
# ---------------------------------------------------------------------------

def _load_comfyui_workflow(workflow_id: str) -> dict:
    """Carrega o JSON de um workflow ComfyUI do diretório workflows/."""
    path = _WORKFLOWS_DIR / workflow_id / "comfyui.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Workflow ComfyUI não encontrado: '{workflow_id}'. Esperado em: {path}"
        )
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


async def _comfyui_status() -> dict:
    """Consulta disponibilidade, versão e estado da fila do ComfyUI."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            t0 = time.monotonic()
            r_stats = await client.get(f"{_COMFYUI_URL}/system_stats")
            latency_ms = int((time.monotonic() - t0) * 1000)

            if r_stats.status_code != 200:
                return {"available": False, "latency_ms": latency_ms}

            stats = r_stats.json()
            r_queue = await client.get(f"{_COMFYUI_URL}/queue")
            queue = r_queue.json() if r_queue.status_code == 200 else {}

            return {
                "available": True,
                "latency_ms": latency_ms,
                "version": stats.get("system", {}).get("comfyui_version", "unknown"),
                "python_version": stats.get("system", {}).get("python_version", "unknown"),
                "queue_pending": len(queue.get("queue_pending", [])),
                "queue_running": len(queue.get("queue_running", [])),
            }
    except Exception:
        return {"available": False, "latency_ms": None}


async def _comfyui_upload_image(
    client: httpx.AsyncClient,
    image_data: bytes,
    filename: str = "input.png",
) -> str:
    """Faz upload de uma imagem para o ComfyUI. Retorna o nome do arquivo no servidor."""
    r = await client.post(
        f"{_COMFYUI_URL}/upload/image",
        files={"image": (filename, image_data, "image/png")},
        data={"type": "input"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["name"]


async def _comfyui_submit(client: httpx.AsyncClient, workflow: dict) -> str:
    """Submete um workflow ao ComfyUI. Retorna o prompt_id."""
    r = await client.post(
        f"{_COMFYUI_URL}/prompt",
        json={"prompt": workflow, "client_id": _CLIENT_ID},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("node_errors"):
        raise RuntimeError(f"Erros nos nodes do workflow: {data['node_errors']}")
    return data["prompt_id"]


async def _comfyui_poll(client: httpx.AsyncClient, prompt_id: str, timeout: int = 120) -> dict:
    """Aguarda conclusão de um job via polling do histórico do ComfyUI."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        r = await client.get(f"{_COMFYUI_URL}/history/{prompt_id}", timeout=10)
        r.raise_for_status()
        data = r.json()
        if prompt_id in data:
            return data[prompt_id]
        await asyncio.sleep(2)
    raise TimeoutError(f"Workflow '{prompt_id}' não completou em {timeout}s")


async def _comfyui_download_image(
    client: httpx.AsyncClient,
    filename: str,
    subfolder: str = "",
) -> str:
    """Baixa uma imagem do output do ComfyUI e retorna como base64."""
    r = await client.get(
        f"{_COMFYUI_URL}/view",
        params={"filename": filename, "subfolder": subfolder, "type": "output"},
        timeout=30,
    )
    r.raise_for_status()
    return base64.b64encode(r.content).decode("utf-8")


def _parse_comfyui_images(history_entry: dict) -> list[dict]:
    """Extrai a lista de imagens geradas a partir do histórico do ComfyUI."""
    images = []
    for node_id, node_output in history_entry.get("outputs", {}).items():
        for img in node_output.get("images", []):
            images.append({
                "filename": img.get("filename", ""),
                "subfolder": img.get("subfolder", ""),
                "type": img.get("type", "output"),
                "node_id": node_id,
            })
    return images


# ---------------------------------------------------------------------------
# Workflows
# ---------------------------------------------------------------------------

async def _echo(job_input: dict) -> dict:
    """Devolve exatamente o que recebeu."""
    return job_input


async def _health(job_input: dict) -> dict:
    """Retorna informações do ambiente de execução, GPU e estado do ComfyUI."""
    now = datetime.now(timezone.utc)
    comfyui = await _comfyui_status()
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
        "comfyui": comfyui,
        "directories": {
            "workflows": str(_WORKFLOWS_DIR),
            "workflows_available": [
                str(p.parent.relative_to(_WORKFLOWS_DIR))
                for p in _WORKFLOWS_DIR.rglob("comfyui.json")
            ],
        },
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


async def _image_identity(job_input: dict) -> dict:
    """
    Carrega uma imagem no ComfyUI e a retorna sem modificação.
    Valida o fluxo completo: upload → execução → parsing → retorno.

    Input: {"image": "<base64>"}
    Output: {"prompt_id": "...", "images": [...], "image_b64": "..."}
    """
    image_b64 = job_input.get("image")
    if not image_b64:
        raise ValueError("Campo obrigatório ausente: 'image' (base64)")

    try:
        image_data = base64.b64decode(image_b64)
    except Exception as exc:
        raise ValueError(f"Valor inválido para 'image': não é base64 válido. {exc}") from exc

    t_comfyui = time.monotonic()
    async with httpx.AsyncClient() as client:
        # 1. Upload da imagem
        uploaded_filename = await _comfyui_upload_image(client, image_data)

        # 2. Carregar e parametrizar o workflow
        workflow = _load_comfyui_workflow("image/identity")
        workflow["1"]["inputs"]["image"] = uploaded_filename

        # 3. Submeter e aguardar
        prompt_id = await _comfyui_submit(client, workflow)
        history_entry = await _comfyui_poll(client, prompt_id, timeout=120)
        comfyui_ms = int((time.monotonic() - t_comfyui) * 1000)

        # 4. Parsear e baixar resultado
        output_images = _parse_comfyui_images(history_entry)
        if not output_images:
            raise RuntimeError("ComfyUI não retornou imagens no output")

        first = output_images[0]
        result_b64 = await _comfyui_download_image(
            client, first["filename"], first["subfolder"]
        )

    return {
        "prompt_id": prompt_id,
        "images": output_images,
        "image_b64": result_b64,
        "comfyui_ms": comfyui_ms,
    }


_WORKFLOWS: dict[str, object] = {
    "echo": _echo,
    "health": _health,
    "image-echo": _image_echo,
    "image-identity": _image_identity,
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
                "vram_free_mb": _GPU_INFO["vram_free_mb"],
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
print(f"[ratec] ComfyUI URL: {_COMFYUI_URL}", flush=True)
print(f"[ratec] Workflows dir: {_WORKFLOWS_DIR}", flush=True)

runpod.serverless.start({"handler": handler})
