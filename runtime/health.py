from __future__ import annotations

import platform
import shutil
import socket
import subprocess
import time
from typing import Any

import httpx

from runtime.configuration import RuntimeConfig
from runtime.observability import get_gpu


async def check_comfyui(config: RuntimeConfig) -> dict[str, Any]:
    """Verifica disponibilidade, versão, fila e latência do ComfyUI."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            t0 = time.monotonic()
            r_stats = await client.get(f"{config.comfyui_url}/system_stats")
            latency_ms = int((time.monotonic() - t0) * 1000)

            if r_stats.status_code != 200:
                return {"available": False, "latency_ms": latency_ms}

            system = r_stats.json().get("system", {})
            r_queue = await client.get(f"{config.comfyui_url}/queue")
            queue = r_queue.json() if r_queue.status_code == 200 else {}

            return {
                "available": True,
                "latency_ms": latency_ms,
                "version": system.get("comfyui_version", "unknown"),
                "python_version": system.get("python_version", "unknown"),
                "torch_version": system.get("torch_version", "unknown"),
                "queue_pending": len(queue.get("queue_pending", [])),
                "queue_running": len(queue.get("queue_running", [])),
            }
    except Exception:
        return {"available": False, "latency_ms": None}


def check_gpu() -> dict[str, Any]:
    """Retorna informações da GPU e versão do driver CUDA."""
    gpu = get_gpu()
    driver_version = None
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0:
            driver_version = r.stdout.strip()
    except Exception:
        pass

    return {
        "model": gpu.model,
        "driver_version": driver_version,
        "vram_total_mb": gpu.vram_total_mb,
        "vram_used_mb": gpu.vram_used_mb,
        "vram_free_mb": gpu.vram_free_mb,
    }


def check_comfyui_manager(config: RuntimeConfig) -> dict[str, Any]:
    """Verifica se o ComfyUI Manager está instalado."""
    manager_path = config.comfyui_path / "custom_nodes" / "ComfyUI-Manager"
    installed = manager_path.exists()
    version = None
    if installed:
        version_file = manager_path / "version.txt"
        if version_file.exists():
            version = version_file.read_text().strip()
    return {"installed": installed, "version": version}


def check_storage(config: RuntimeConfig) -> dict[str, Any]:
    """Verifica espaço em disco e disponibilidade do Network Volume."""
    info: dict[str, Any] = {"volume_available": config.volume_available}

    if config.volume_available:
        try:
            usage = shutil.disk_usage(config.volume_path)
            info["volume_total_gb"] = round(usage.total / (1024 ** 3), 2)
            info["volume_used_gb"] = round(usage.used / (1024 ** 3), 2)
            info["volume_free_gb"] = round(usage.free / (1024 ** 3), 2)
        except Exception:
            pass

        required = [
            "models/checkpoints", "models/vae", "models/loras",
            "models/controlnet", "output", "input", "temp", "logs",
        ]
        info["directories"] = {d: (config.volume_path / d).exists() for d in required}

    try:
        local = shutil.disk_usage("/")
        info["local_disk_free_gb"] = round(local.free / (1024 ** 3), 2)
    except Exception:
        pass

    return info


async def full_health(config: RuntimeConfig) -> dict[str, Any]:
    """Retorna diagnóstico completo do ambiente de execução."""
    return {
        "runtime_version": config.version,
        "environment": config.environment,
        "python_version": platform.python_version(),
        "hostname": socket.gethostname(),
        "gpu": check_gpu(),
        "comfyui": await check_comfyui(config),
        "comfyui_manager": check_comfyui_manager(config),
        "storage": check_storage(config),
    }
