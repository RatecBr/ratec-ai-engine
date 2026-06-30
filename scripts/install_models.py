#!/usr/bin/env python3
"""
RATEC AI ENGINE — Model Installation Manager
Instala e valida modelos no Network Volume para o AI Runtime.

Uso:
  python scripts/install_models.py
  HF_TOKEN=hf_xxx python scripts/install_models.py

Variáveis de ambiente:
  RUNPOD_VOLUME_PATH  — caminho do Network Volume (padrão: /runpod-volume)
  COMFYUI_PATH        — caminho da instalação do ComfyUI (padrão: /comfyui)
  HF_TOKEN            — token HuggingFace (necessário para modelos comerciais como BRIA RMBG)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

# ── Paths ──────────────────────────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).parent
_REPO_ROOT = _SCRIPT_DIR.parent
_WORKFLOWS_DIR = _REPO_ROOT / "workflows"

VOLUME = Path(os.getenv("RUNPOD_VOLUME_PATH", "/runpod-volume"))
COMFYUI = Path(os.getenv("COMFYUI_PATH", "/comfyui"))


# ── Model registry ─────────────────────────────────────────────────────────
class ModelSpec(NamedTuple):
    id: str
    name: str
    version: str
    download_url: str
    dest_subpath: str        # relativo ao VOLUME
    size_mb: int
    custom_node_name: str | None
    custom_node_url: str | None
    workflow_id: str
    capability: str


TARGET_MODELS: list[ModelSpec] = [
    ModelSpec(
        id="bria-rmbg-1.4",
        name="BRIA RMBG-1.4",
        version="1.4",
        download_url="https://huggingface.co/briaai/RMBG-1.4/resolve/main/model.pth",
        dest_subpath="models/BRIA/RMBG-1.4.pth",
        size_mb=176,
        custom_node_name="ComfyUI-BRIA_AI-RMBG",
        custom_node_url="https://github.com/BRIA-AI/ComfyUI-BRIA_AI-RMBG",
        workflow_id="image/background-remove",
        capability="background-remove",
    ),
    ModelSpec(
        id="realesrgan-x4plus",
        name="RealESRGAN x4plus",
        version="0.3.0",
        download_url="https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
        dest_subpath="models/upscale_models/RealESRGAN_x4plus.pth",
        size_mb=64,
        custom_node_name=None,
        custom_node_url=None,
        workflow_id="image/image-upscale",
        capability="image-upscale",
    ),
]


# ── Result container ────────────────────────────────────────────────────────
class ModelResult:
    def __init__(self, spec: ModelSpec) -> None:
        self.spec = spec
        self.already_installed: bool = False
        self.download_ok: bool = False
        self.download_error: str = ""
        self.download_time_s: float = 0.0
        self.file_size_bytes: int = 0
        self.custom_node_ok: bool = spec.custom_node_name is None
        self.custom_node_msg: str = ""
        self.workflow_ok: bool = False
        self.workflow_error: str = ""

    @property
    def installed(self) -> bool:
        return self.already_installed or self.download_ok


# ── Helpers ─────────────────────────────────────────────────────────────────
def _log(msg: str) -> None:
    print(f"[ratec-install] {msg}", flush=True)


def _check_volume() -> tuple[bool, str]:
    if not VOLUME.exists():
        return False, f"não encontrado em {VOLUME}"
    if not VOLUME.is_dir():
        return False, f"{VOLUME} não é um diretório"
    try:
        test = VOLUME / ".ratec_probe"
        test.touch()
        test.unlink()
    except OSError as exc:
        return False, f"sem permissão de escrita: {exc}"
    return True, str(VOLUME)


def _download(url: str, dest: Path, size_mb: int, token: str | None) -> tuple[bool, str, float]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    headers: dict[str, str] = {"User-Agent": "ratec-model-installer/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    t0 = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            total = int(resp.headers.get("Content-Length", 0)) or size_mb * 1_000_000
            downloaded = 0
            with open(dest, "wb") as fh:
                while True:
                    chunk = resp.read(1024 * 1024)
                    if not chunk:
                        break
                    fh.write(chunk)
                    downloaded += len(chunk)
                    pct = min(downloaded * 100 // total, 100) if total else 0
                    print(
                        f"\r  {downloaded / 1_000_000:.1f}MB / ~{size_mb}MB ({pct}%)",
                        end="", flush=True,
                    )
            print()
        return True, "", time.monotonic() - t0
    except Exception as exc:
        dest.unlink(missing_ok=True)
        return False, str(exc), time.monotonic() - t0


def _install_custom_node(name: str, url: str) -> tuple[bool, str]:
    node_dir = COMFYUI / "custom_nodes" / name
    if node_dir.exists():
        return True, "já instalado"

    custom_nodes_dir = COMFYUI / "custom_nodes"
    if not custom_nodes_dir.exists():
        return False, f"diretório não encontrado: {custom_nodes_dir}"

    try:
        result = subprocess.run(
            ["git", "clone", "--depth=1", url, str(node_dir)],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            return False, result.stderr.strip()

        req_file = node_dir / "requirements.txt"
        if req_file.exists():
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(req_file), "-q"],
                timeout=300,
            )
        return True, "instalado"
    except Exception as exc:
        return False, str(exc)


def _workflow_health_check(spec: ModelSpec) -> tuple[bool, str]:
    wf_path = _WORKFLOWS_DIR / spec.workflow_id / "comfyui.json"
    if not wf_path.exists():
        return False, f"workflow não encontrado: {wf_path}"
    try:
        with open(wf_path) as fh:
            workflow = json.load(fh)
        if not workflow:
            return False, "workflow vazio"
    except json.JSONDecodeError as exc:
        return False, f"JSON inválido: {exc}"

    model_dest = VOLUME / spec.dest_subpath
    if not model_dest.exists():
        return False, f"modelo não encontrado em: {model_dest}"
    if model_dest.stat().st_size < 1_000:
        return False, f"arquivo suspeito — tamanho: {model_dest.stat().st_size} bytes"

    return True, "OK"


def _generate_report(volume_ok: bool, results: list[ModelResult], started_at: str) -> dict:
    return {
        "ratec_ai_engine": "model-installation-report",
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "started_at": started_at,
        "network_volume": {
            "path": str(VOLUME),
            "mounted": volume_ok,
        },
        "models": [
            {
                "id": r.spec.id,
                "name": r.spec.name,
                "version": r.spec.version,
                "capability": r.spec.capability,
                "path": str(VOLUME / r.spec.dest_subpath),
                "size_mb": r.spec.size_mb,
                "file_size_mb": round(r.file_size_bytes / 1_000_000, 2) if r.file_size_bytes else None,
                "status": (
                    "already_installed" if r.already_installed
                    else "installed" if r.download_ok
                    else "failed"
                ),
                "download_error": r.download_error or None,
                "download_time_s": round(r.download_time_s, 1) if r.download_ok else None,
                "custom_node": {
                    "name": r.spec.custom_node_name,
                    "status": "ok" if r.custom_node_ok else "failed",
                    "message": r.custom_node_msg or None,
                } if r.spec.custom_node_name else None,
                "health_check": {
                    "workflow": r.spec.workflow_id,
                    "status": "ok" if r.workflow_ok else "failed",
                    "error": r.workflow_error or None,
                },
            }
            for r in results
        ],
        "summary": {
            "total": len(results),
            "installed": sum(1 for r in results if r.installed),
            "failed": sum(1 for r in results if not r.installed),
            "health_checks_passed": sum(1 for r in results if r.workflow_ok),
            "ready_for_playground": all(r.installed and r.workflow_ok for r in results),
        },
    }


# ── Main ────────────────────────────────────────────────────────────────────
def main() -> int:
    started_at = datetime.now(timezone.utc).isoformat()
    hf_token = os.getenv("HF_TOKEN")

    _log("=" * 60)
    _log("RATEC AI ENGINE — Model Installation Manager v1.0")
    _log("=" * 60)

    if not hf_token:
        _log("AVISO: HF_TOKEN não configurado.")
        _log("  O BRIA RMBG-1.4 é um modelo comercial com licença em HuggingFace.")
        _log("  Se o download falhar, configure: export HF_TOKEN=hf_xxx")

    # 1. Verificar Network Volume
    _log("")
    _log("1. Verificando Network Volume...")
    volume_ok, volume_msg = _check_volume()
    if volume_ok:
        _log(f"   OK: {volume_msg}")
    else:
        _log(f"   ERRO: {volume_msg}")
        _log("   O Network Volume deve estar montado antes de instalar modelos.")

    results: list[ModelResult] = []

    for spec in TARGET_MODELS:
        _log("")
        _log(f"── {spec.name} ({spec.id}) ──")
        r = ModelResult(spec)
        results.append(r)

        if not volume_ok:
            r.download_error = "Network Volume não disponível"
            _log("   PULADO — volume não disponível")
            continue

        # 2. Verificar se já está instalado
        dest = VOLUME / spec.dest_subpath
        if dest.exists() and dest.stat().st_size > 1_000:
            r.already_installed = True
            r.file_size_bytes = dest.stat().st_size
            _log(f"   Já instalado: {dest} ({r.file_size_bytes / 1_000_000:.1f}MB)")
        else:
            # 3. Download do modelo
            _log(f"   URL: {spec.download_url}")
            _log(f"   Destino: {dest}")
            _log(f"   Tamanho esperado: ~{spec.size_mb}MB")

            ok, err, elapsed = _download(spec.download_url, dest, spec.size_mb, hf_token)
            r.download_ok = ok
            r.download_error = err
            r.download_time_s = elapsed

            if ok:
                r.file_size_bytes = dest.stat().st_size
                _log(f"   Download OK — {r.file_size_bytes / 1_000_000:.1f}MB em {elapsed:.1f}s")
            else:
                _log(f"   ERRO: {err}")
                if "403" in err and "huggingface" in spec.download_url:
                    _log("   DICA: modelo requer autenticação. Configure HF_TOKEN.")

        # 4. Instalar custom node
        if spec.custom_node_name and spec.custom_node_url:
            _log(f"   Custom node: {spec.custom_node_name}")
            node_ok, node_msg = _install_custom_node(spec.custom_node_name, spec.custom_node_url)
            r.custom_node_ok = node_ok
            r.custom_node_msg = node_msg
            _log(f"   Custom node: {'OK' if node_ok else 'ERRO'} — {node_msg}")

        # 5. Health check do workflow
        _log(f"   Health check: {spec.workflow_id}")
        wf_ok, wf_err = _workflow_health_check(spec)
        r.workflow_ok = wf_ok
        r.workflow_error = wf_err
        _log(f"   Health check: {'OK' if wf_ok else f'FALHOU — {wf_err}'}")

    # 6. Relatório
    report = _generate_report(volume_ok, results, started_at)

    _log("")
    _log("=" * 60)
    _log("RELATÓRIO")
    _log("=" * 60)
    print(json.dumps(report, indent=2, ensure_ascii=False))

    if volume_ok:
        try:
            log_dir = VOLUME / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = log_dir / f"install_report_{ts}.json"
            report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
            _log(f"Relatório salvo: {report_path}")
        except Exception as exc:
            _log(f"AVISO: não foi possível salvar o relatório: {exc}")

    summary = report["summary"]
    _log("")
    _log(f"Total: {summary['total']} | Instalados: {summary['installed']} | Falhas: {summary['failed']}")
    _log(f"Health checks: {summary['health_checks_passed']}/{summary['total']} OK")
    _log("")

    if summary["ready_for_playground"]:
        _log("PRONTO — plataforma pronta para iniciar testes no AI Playground")
        return 0
    else:
        _log("FALHAS DETECTADAS — verificar erros acima antes de iniciar testes")
        return 1


if __name__ == "__main__":
    sys.exit(main())
