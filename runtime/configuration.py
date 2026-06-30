from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RuntimeConfig:
    """
    Fonte única de verdade para toda configuração do AI Runtime.
    Carregada a partir de variáveis de ambiente; nunca hardcodada no código.
    """

    # ── Versioning ────────────────────────────────────────────────────────────
    version: str = "1.0.0"

    # ── Environment ───────────────────────────────────────────────────────────
    environment: str = field(
        default_factory=lambda: os.getenv("ENVIRONMENT", "production")
    )

    # ── Paths ─────────────────────────────────────────────────────────────────
    volume_path: Path = field(
        default_factory=lambda: Path(os.getenv("RUNPOD_VOLUME_PATH", "/runpod-volume"))
    )
    workflows_dir: Path = field(
        default_factory=lambda: Path(
            os.getenv("WORKFLOWS_DIR", str(Path(__file__).parent.parent / "workflows"))
        )
    )
    comfyui_path: Path = field(
        default_factory=lambda: Path(os.getenv("COMFYUI_PATH", "/comfyui"))
    )

    # ── ComfyUI ───────────────────────────────────────────────────────────────
    comfyui_url: str = field(
        default_factory=lambda: os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")
    )
    comfyui_port: int = field(
        default_factory=lambda: int(os.getenv("COMFYUI_PORT", "8188"))
    )
    comfyui_startup_timeout: int = field(
        default_factory=lambda: int(os.getenv("COMFYUI_READY_TIMEOUT", "120"))
    )

    # ── Execution ─────────────────────────────────────────────────────────────
    job_timeout: int = field(
        default_factory=lambda: int(os.getenv("JOB_TIMEOUT", "300"))
    )
    poll_interval: float = 2.0

    @classmethod
    def from_env(cls) -> "RuntimeConfig":
        return cls()

    # ── Derived paths ─────────────────────────────────────────────────────────

    @property
    def models_dir(self) -> Path:
        return self.volume_path / "models"

    @property
    def output_dir(self) -> Path:
        return self.volume_path / "output"

    @property
    def input_dir(self) -> Path:
        return self.volume_path / "input"

    @property
    def temp_dir(self) -> Path:
        return self.volume_path / "temp"

    @property
    def logs_dir(self) -> Path:
        return self.volume_path / "logs"

    @property
    def volume_available(self) -> bool:
        return self.volume_path.exists()

    @property
    def active_models_path(self) -> Path:
        """Caminho para o arquivo active_models.json no Network Volume."""
        return self.volume_path / "active_models.json"

    def load_active_models(self) -> dict[str, str]:
        """
        Lê o active_models.json do Network Volume.
        Formato: {"image/background-remove": "birefnet", ...}
        Retorna {} se o arquivo não existir ou estiver corrompido.
        """
        import json as _json
        try:
            with open(self.active_models_path, encoding="utf-8") as f:
                data = _json.load(f)
            return {k: v for k, v in data.items() if not k.startswith("_")}
        except (FileNotFoundError, _json.JSONDecodeError, OSError):
            return {}
