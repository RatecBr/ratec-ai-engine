from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from typing import Any


@dataclass
class GPUMetrics:
    model: str | None = None
    vram_total_mb: int | None = None
    vram_used_mb: int | None = None
    vram_free_mb: int | None = None


@dataclass
class ExecutionMetrics:
    execution_time_ms: int = 0
    comfyui_time_ms: int | None = None
    upload_time_ms: int | None = None
    download_time_ms: int | None = None
    gpu: GPUMetrics = field(default_factory=GPUMetrics)

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_time_ms": self.execution_time_ms,
            "comfyui_time_ms": self.comfyui_time_ms,
            "upload_time_ms": self.upload_time_ms,
            "download_time_ms": self.download_time_ms,
            "gpu_model": self.gpu.model,
            "vram_total_mb": self.gpu.vram_total_mb,
            "vram_used_mb": self.gpu.vram_used_mb,
            "vram_free_mb": self.gpu.vram_free_mb,
        }


def _collect_gpu() -> GPUMetrics:
    """Coleta métricas de GPU via nvidia-smi sem referenciar modelos específicos."""
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
            return GPUMetrics(
                model=parts[0] if len(parts) > 0 else None,
                vram_total_mb=int(parts[1]) if len(parts) > 1 else None,
                vram_used_mb=int(parts[2]) if len(parts) > 2 else None,
                vram_free_mb=int(parts[3]) if len(parts) > 3 else None,
            )
    except Exception:
        pass
    return GPUMetrics()


# Capturado uma vez no boot — hardware da GPU não muda durante o worker
_GPU: GPUMetrics = _collect_gpu()


def get_gpu() -> GPUMetrics:
    return _GPU
