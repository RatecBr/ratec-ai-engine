"""
RATEC AI Runtime
================
Módulo de execução de IA da plataforma RATEC.

Responsabilidades:
  - inicialização e configuração do ambiente
  - upload e download de arquivos
  - execução de workflows via ComfyUI
  - observabilidade (GPU, timing, health)
  - health check completo do ambiente

O handler.py (ponto de entrada RunPod) delega toda lógica a Runtime.handle().
Nenhuma regra de negócio dos aplicativos consumidores existe nesta camada.
"""
from __future__ import annotations

import base64
import platform
import socket
import time
from datetime import datetime, timezone
from typing import Any

import httpx

from runtime.configuration import RuntimeConfig
from runtime.download import download_image
from runtime.executor import ComfyUIExecutor
from runtime.health import full_health
from runtime.observability import ExecutionMetrics, get_gpu
from runtime.upload import upload_image
from runtime.workflow import WorkflowManager

VERSION = "1.0.0"
_BOOT_TIME = datetime.now(timezone.utc)


class Runtime:
    """
    Fachada principal do AI Runtime.
    Recebe um job RunPod, despacha para o workflow correto e retorna o resultado.
    """

    def __init__(
        self,
        config: RuntimeConfig,
        executor: ComfyUIExecutor,
        workflow_manager: WorkflowManager,
    ) -> None:
        self._config = config
        self._executor = executor
        self._wm = workflow_manager

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    def initialize(cls) -> "Runtime":
        config = RuntimeConfig.from_env()
        instance = cls(
            config=config,
            executor=ComfyUIExecutor(config),
            workflow_manager=WorkflowManager(config.workflows_dir),
        )
        instance._print_startup()
        return instance

    # ── Entry point ───────────────────────────────────────────────────────────

    async def handle(self, job: dict) -> dict:
        t_start = time.monotonic()
        job_input: dict = job.get("input", {})
        workflow_id: str | None = job_input.get("workflow_id")

        if not workflow_id:
            return {"status": "failed", "error": "Campo obrigatório ausente: 'workflow_id'"}

        _dispatch = {
            "echo": self._echo,
            "health": self._health,
            "image-echo": self._image_echo,
            "image-identity": self._image_identity,
        }

        fn = _dispatch.get(workflow_id)
        if fn is None:
            return {
                "status": "failed",
                "error": f"Workflow desconhecido: '{workflow_id}'. Disponíveis: {list(_dispatch)}",
            }

        gpu = get_gpu()
        try:
            result = await fn(job_input.get("input", {}))
            return {
                "status": "completed",
                "workflow_id": workflow_id,
                "result": result,
                "observability": {
                    "execution_time_ms": int((time.monotonic() - t_start) * 1000),
                    "gpu_model": gpu.model,
                    "vram_total_mb": gpu.vram_total_mb,
                    "vram_used_mb": gpu.vram_used_mb,
                    "vram_free_mb": gpu.vram_free_mb,
                },
            }
        except Exception as exc:
            return {
                "status": "failed",
                "workflow_id": workflow_id,
                "error": str(exc),
                "observability": {
                    "execution_time_ms": int((time.monotonic() - t_start) * 1000),
                    "gpu_model": gpu.model,
                },
            }

    # ── Workflows ─────────────────────────────────────────────────────────────

    async def _echo(self, job_input: dict) -> dict:
        return job_input

    async def _health(self, job_input: dict) -> dict:
        now = datetime.now(timezone.utc)
        health = await full_health(self._config)
        return {
            **health,
            "boot_time": _BOOT_TIME.isoformat(),
            "timestamp": now.isoformat(),
            "uptime_seconds": int((now - _BOOT_TIME).total_seconds()),
            "worker_ready": True,
            "workflows_available": self._wm.list_available(),
        }

    async def _image_echo(self, job_input: dict) -> dict:
        url = job_input.get("url")
        if not url:
            raise ValueError("Campo obrigatório ausente: 'url'")
        t0 = time.monotonic()
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            r = await client.head(url)
            r.raise_for_status()
        latency_ms = int((time.monotonic() - t0) * 1000)
        content_type = r.headers.get("content-type", "")
        if not content_type.startswith("image/"):
            raise ValueError(f"URL não aponta para imagem: content-type='{content_type}'")
        return {
            "url": url, "accessible": True, "content_type": content_type,
            "content_length": r.headers.get("content-length"),
            "status_code": r.status_code, "latency_ms": latency_ms,
        }

    async def _image_identity(self, job_input: dict) -> dict:
        image_b64 = job_input.get("image")
        if not image_b64:
            raise ValueError("Campo obrigatório ausente: 'image' (base64)")
        try:
            image_data = base64.b64decode(image_b64)
        except Exception as exc:
            raise ValueError(f"'image' não é base64 válido: {exc}") from exc

        async with httpx.AsyncClient() as client:
            filename, upload_ms = await upload_image(client, self._config, image_data)

            workflow = self._wm.load_comfyui("image/identity")
            workflow["1"]["inputs"]["image"] = filename

            t_exec = time.monotonic()
            prompt_id = await self._executor.submit(client, workflow)
            history = await self._executor.poll(client, prompt_id)
            exec_ms = int((time.monotonic() - t_exec) * 1000)

            images = self._executor.parse_images(history)
            if not images:
                raise RuntimeError("ComfyUI não retornou imagens")

            first = images[0]
            result_b64, download_ms = await download_image(
                client, self._config, first["filename"], first["subfolder"]
            )

        return {
            "prompt_id": prompt_id,
            "images": images,
            "image_b64": result_b64,
            "timing": {
                "upload_ms": upload_ms,
                "execution_ms": exec_ms,
                "download_ms": download_ms,
            },
        }

    # ── Startup log ───────────────────────────────────────────────────────────

    def _print_startup(self) -> None:
        gpu = get_gpu()
        print(f"[ratec] RATEC AI Runtime v{VERSION}", flush=True)
        print(f"[ratec] Python {platform.python_version()} | Host: {socket.gethostname()}", flush=True)
        print(f"[ratec] GPU: {gpu.model or 'não detectada'} | VRAM: {gpu.vram_total_mb} MB", flush=True)
        print(f"[ratec] ComfyUI: {self._config.comfyui_url}", flush=True)
        print(f"[ratec] Workflows: {self._config.workflows_dir}", flush=True)
        print(f"[ratec] Volume: {self._config.volume_path} (disponível: {self._config.volume_available})", flush=True)
