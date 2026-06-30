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

VERSION = "2.0.0"
_BOOT_TIME = datetime.now(timezone.utc)

# Mapeamento capability → workflow_id (caminho no diretório workflows/)
# Os aplicativos solicitam a capability; o Runtime resolve qual workflow usar.
_CAPABILITY_ROUTES: dict[str, str] = {
    "background-remove": "image/background-remove",
    "image-upscale": "image/image-upscale",
    "face-segmentation": "image/face-segmentation",
    "haircut": "image/haircut",
    "beard": "image/beard",
    "makeup": "image/makeup",
    "virtual-try-on": "image/virtual-try-on",
    # aliases de backward compatibility
    "image-identity": "image/identity",
    "identity": "image/identity",
}


class Runtime:
    """
    Fachada principal do AI Runtime.
    Recebe um job RunPod, resolve a capability, executa via ComfyUI e retorna o resultado.
    Novos workflows não requerem alterações aqui — basta adicionar comfyui.json + manifest.yaml.
    """

    def __init__(
        self,
        config: RuntimeConfig,
        executor: ComfyUIExecutor,
        workflow_manager: WorkflowManager,
        active_models: dict[str, str] | None = None,
    ) -> None:
        self._config = config
        self._executor = executor
        self._wm = workflow_manager
        # Mapa workflow_id → model_id instalado (lido do active_models.json no volume)
        self._active_models: dict[str, str] = active_models or {}

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    def initialize(cls) -> "Runtime":
        config = RuntimeConfig.from_env()
        active_models = config.load_active_models()
        instance = cls(
            config=config,
            executor=ComfyUIExecutor(config),
            workflow_manager=WorkflowManager(config.workflows_dir),
            active_models=active_models,
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

        gpu = get_gpu()
        try:
            result = await self._dispatch(workflow_id, job_input.get("input", {}))
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

    # ── Dispatcher ────────────────────────────────────────────────────────────

    async def _dispatch(self, workflow_id: str, job_input: dict) -> dict:
        """
        Roteia o job para o handler correto.
        Handlers de sistema têm prioridade; qualquer outro ID é resolvido
        como capability → workflow ComfyUI.
        """
        _system_handlers = {
            "echo": self._echo,
            "health": self._health,
            "image-echo": self._image_echo,
        }

        fn = _system_handlers.get(workflow_id)
        if fn is not None:
            return await fn(job_input)

        # Resolve capability → workflow_id
        resolved = _CAPABILITY_ROUTES.get(workflow_id, workflow_id)

        if not self._wm.exists(resolved):
            available = list(_CAPABILITY_ROUTES.keys()) + list(_system_handlers.keys())
            raise ValueError(
                f"Capability ou workflow desconhecido: '{workflow_id}'. "
                f"Disponíveis: {sorted(available)}"
            )

        return await self._execute_comfyui(resolved, job_input)

    # ── Executor genérico ComfyUI ─────────────────────────────────────────────

    async def _execute_comfyui(self, workflow_id: str, job_input: dict) -> dict:
        """
        Executor genérico para qualquer workflow ComfyUI.
        Convenção: node "1" é sempre o LoadImage (input principal).
        node_overrides adicionais podem ser passados no job_input.
        """
        image_b64: str | None = job_input.get("image")
        node_overrides: dict[str, dict] = dict(job_input.get("node_overrides", {}))

        active_model = self._active_models.get(workflow_id)
        workflow = self._wm.load_comfyui(workflow_id, model_id=active_model)

        async with httpx.AsyncClient() as client:
            upload_ms = 0

            if image_b64:
                try:
                    image_data = base64.b64decode(image_b64)
                except Exception as exc:
                    raise ValueError(f"'image' não é base64 válido: {exc}") from exc

                filename, upload_ms = await upload_image(client, self._config, image_data)
                node_overrides.setdefault("1", {})["image"] = filename

            if node_overrides:
                workflow = self._wm.apply_node_overrides(workflow, node_overrides)

            t_exec = time.monotonic()
            prompt_id = await self._executor.submit(client, workflow)
            history = await self._executor.poll(client, prompt_id)
            exec_ms = int((time.monotonic() - t_exec) * 1000)

            images = self._executor.parse_images(history)
            if not images:
                raise RuntimeError(f"Workflow '{workflow_id}' não retornou imagens")

            result_images = []
            total_download_ms = 0
            for img in images:
                img_b64, dl_ms = await download_image(
                    client, self._config, img["filename"], img["subfolder"]
                )
                total_download_ms += dl_ms
                result_images.append({**img, "image_b64": img_b64})

        return {
            "prompt_id": prompt_id,
            "images": result_images,
            "timing": {
                "upload_ms": upload_ms,
                "execution_ms": exec_ms,
                "download_ms": total_download_ms,
            },
        }

    # ── Handlers de sistema ───────────────────────────────────────────────────

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
            "capabilities": sorted(_CAPABILITY_ROUTES.keys()),
            "active_models": self._active_models,
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

    # ── Startup log ───────────────────────────────────────────────────────────

    def _print_startup(self) -> None:
        gpu = get_gpu()
        available = self._wm.list_available()
        print(f"[ratec] RATEC AI Runtime v{VERSION}", flush=True)
        print(f"[ratec] Python {platform.python_version()} | Host: {socket.gethostname()}", flush=True)
        print(f"[ratec] GPU: {gpu.model or 'não detectada'} | VRAM: {gpu.vram_total_mb} MB", flush=True)
        print(f"[ratec] ComfyUI: {self._config.comfyui_url}", flush=True)
        print(f"[ratec] Workflows: {len(available)} disponíveis → {available}", flush=True)
        print(f"[ratec] Capabilities: {sorted(_CAPABILITY_ROUTES.keys())}", flush=True)
        print(f"[ratec] Volume: {self._config.volume_path} (disponível: {self._config.volume_available})", flush=True)
        if self._active_models:
            for wf_id, model_id in self._active_models.items():
                print(f"[ratec] Modelo ativo: {wf_id} → {model_id}", flush=True)
        else:
            print("[ratec] active_models.json não encontrado — usando comfyui.json padrão", flush=True)
