"""
AI Lab — Camada de laboratório do RATEC AI Runtime.
Registra execuções, benchmarks, avaliações e cache experimental.
Não altera o Runtime — é uma extensão observacional.
"""
from __future__ import annotations

import base64
import hashlib
from pathlib import Path

from runtime.lab import database, cache as _cache


class Lab:
    """
    Fachada do AI Lab.
    Inicializada pelo Playground; transparente ao handler de produção RunPod.
    """

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.images_dir = data_dir / "images"
        database.init(data_dir)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        (self.images_dir / "input").mkdir(exist_ok=True)
        (self.images_dir / "output").mkdir(exist_ok=True)

    # ── Imagens ───────────────────────────────────────────────────────────────

    def save_input_image(self, image_b64: str) -> str:
        """Salva imagem de entrada, retorna hash SHA-256 (usado como ID)."""
        data = base64.b64decode(image_b64)
        h = hashlib.sha256(data).hexdigest()
        path = self.images_dir / "input" / f"{h}.png"
        if not path.exists():
            path.write_bytes(data)
        return h

    def save_output_images(self, exec_id: int, images: list[dict]) -> None:
        """Salva imagens de saída de uma execução."""
        out_dir = self.images_dir / "output" / str(exec_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        for i, img in enumerate(images):
            b64 = img.get("image_b64", "")
            if b64:
                out_dir.joinpath(f"{i}.png").write_bytes(base64.b64decode(b64))

    def input_image_path(self, input_hash: str) -> Path:
        return self.images_dir / "input" / f"{input_hash}.png"

    def output_image_path(self, exec_id: int, index: int) -> Path:
        return self.images_dir / "output" / str(exec_id) / f"{index}.png"

    # ── Execuções ─────────────────────────────────────────────────────────────

    def record(
        self,
        *,
        capability: str,
        workflow_id: str,
        job_result: dict,
        input_hash: str | None = None,
        input_params: dict | None = None,
        node_overrides: dict | None = None,
    ) -> int:
        """Persiste uma execução. Retorna o ID do registro."""
        obs = job_result.get("observability", {})
        result = job_result.get("result", {})
        timing = result.get("timing", {})
        images = result.get("images", [])
        success = job_result.get("status") == "completed"

        exec_id = database.save_execution(
            capability=capability,
            workflow_id=workflow_id,
            success=success,
            total_ms=obs.get("execution_time_ms", 0),
            input_hash=input_hash,
            input_params=input_params,
            node_overrides=node_overrides,
            prompt_id=result.get("prompt_id"),
            error_msg=job_result.get("error"),
            upload_ms=timing.get("upload_ms", 0),
            execution_ms=timing.get("execution_ms", 0),
            download_ms=timing.get("download_ms", 0),
            gpu_model=obs.get("gpu_model"),
            vram_total_mb=obs.get("vram_total_mb"),
            vram_used_mb=obs.get("vram_used_mb"),
            vram_free_mb=obs.get("vram_free_mb"),
            output_count=len(images),
        )

        if success and images:
            self.save_output_images(exec_id, images)

        return exec_id

    # ── Cache ─────────────────────────────────────────────────────────────────

    def cache_key(self, workflow_id: str, input_hash: str | None, node_overrides: dict) -> str:
        return _cache.compute_key(workflow_id, input_hash, node_overrides)

    def cache_get(self, key: str) -> str | None:
        return database.cache_get(key)

    def cache_set(self, key: str, capability: str, result_json: str) -> None:
        database.cache_set(key, capability, result_json)
