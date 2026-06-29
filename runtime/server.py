from __future__ import annotations

import subprocess
import time
from pathlib import Path

import httpx

from runtime.configuration import RuntimeConfig


class ComfyUIServer:
    """
    Gerencia o processo do ComfyUI como subprocesso do AI Runtime.
    Usado quando o Runtime precisa iniciar o ComfyUI diretamente
    (ex: ambiente local, testes, deploys sem start.sh).
    """

    def __init__(self, config: RuntimeConfig) -> None:
        self._config = config
        self._process: subprocess.Popen | None = None

    def start(self) -> None:
        """Inicia o ComfyUI em background."""
        self._config.logs_dir.mkdir(parents=True, exist_ok=True)
        log_path = self._config.logs_dir / "comfyui.log"

        print("[ratec-server] Iniciando ComfyUI...", flush=True)
        with open(log_path, "a") as log:
            self._process = subprocess.Popen(
                [
                    "python3",
                    str(self._config.comfyui_path / "main.py"),
                    "--listen", "0.0.0.0",
                    "--port", str(self._config.comfyui_port),
                    "--disable-auto-launch",
                    "--preview-method", "none",
                ],
                cwd=self._config.comfyui_path,
                stdout=log,
                stderr=log,
            )
        print(f"[ratec-server] ComfyUI PID: {self._process.pid}", flush=True)

    def wait_ready(self) -> bool:
        """Aguarda o ComfyUI estar pronto. Retorna False se timeout ou crash."""
        timeout = self._config.comfyui_startup_timeout
        interval = 2
        elapsed = 0

        while elapsed < timeout:
            if self._process and self._process.poll() is not None:
                print("[ratec-server] ERRO: ComfyUI encerrou inesperadamente", flush=True)
                return False
            try:
                with httpx.Client(timeout=2) as c:
                    if c.get(f"{self._config.comfyui_url}/system_stats").status_code == 200:
                        print(f"[ratec-server] ComfyUI pronto após {elapsed}s", flush=True)
                        return True
            except Exception:
                pass
            time.sleep(interval)
            elapsed += interval

        print(f"[ratec-server] ERRO: ComfyUI não iniciou em {timeout}s", flush=True)
        return False

    def is_alive(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def stop(self) -> None:
        if self._process and self.is_alive():
            self._process.terminate()
            try:
                self._process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._process.kill()
            print("[ratec-server] ComfyUI encerrado", flush=True)
