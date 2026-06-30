#!/usr/bin/env python3
"""
RATEC AI ENGINE — Model Installation Manager v2.0
Instala automaticamente o melhor modelo disponível para cada Capability.

Política:
  - Cada Capability possui uma lista ordenada de modelos compatíveis.
  - O instalador tenta instalar o modelo de maior prioridade.
  - Se um modelo exigir autenticação ou falhar, tenta o próximo.
  - Nenhuma Capability falha por indisponibilidade de um modelo específico.
  - Escreve active_models.json no Network Volume após a instalação.

Uso:
  python scripts/install_models.py
  HF_TOKEN=hf_xxx python scripts/install_models.py   (necessário para BRIA RMBG)

Variáveis de ambiente:
  RUNPOD_VOLUME_PATH  — Network Volume (padrão: /runpod-volume)
  COMFYUI_PATH        — Instalação do ComfyUI (padrão: /comfyui)
  HF_TOKEN            — Token HuggingFace (modelos comerciais/privados)
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
_REPO_ROOT = Path(__file__).parent.parent
_WORKFLOWS_DIR = _REPO_ROOT / "workflows"

VOLUME = Path(os.getenv("RUNPOD_VOLUME_PATH", "/runpod-volume"))
COMFYUI = Path(os.getenv("COMFYUI_PATH", "/comfyui"))


# ── Model spec ─────────────────────────────────────────────────────────────
class ModelSpec(NamedTuple):
    id: str
    name: str
    version: str
    download_url: str | None       # None = modelo baixado automaticamente pelo custom node
    dest_subpath: str | None       # relativo ao VOLUME; None = sem arquivo pré-instalado
    size_mb: int
    requires_hf_token: bool
    custom_node_name: str | None
    custom_node_url: str | None
    workflow_id: str               # ex: "image/background-remove"
    capability: str                # ex: "background-remove"
    download_strategy: str         # direct_url | hf_hub | custom_node_auto


# ── Capability priority lists ───────────────────────────────────────────────
# A ordem define a prioridade: o primeiro modelo disponível e instalável é escolhido.
CAPABILITY_PRIORITIES: dict[str, list[ModelSpec]] = {
    "image/background-remove": [
        ModelSpec(
            id="bria-rmbg-1.4",
            name="BRIA RMBG-1.4",
            version="1.4",
            download_url="https://huggingface.co/briaai/RMBG-1.4/resolve/main/model.pth",
            dest_subpath="models/BRIA/RMBG-1.4.pth",
            size_mb=176,
            requires_hf_token=True,
            custom_node_name="ComfyUI-BRIA_AI-RMBG",
            custom_node_url="https://github.com/BRIA-AI/ComfyUI-BRIA_AI-RMBG",
            workflow_id="image/background-remove",
            capability="background-remove",
            download_strategy="hf_hub",
        ),
        ModelSpec(
            id="birefnet",
            name="BiRefNet",
            version="1.0",
            download_url=None,
            dest_subpath=None,
            size_mb=180,
            requires_hf_token=False,
            custom_node_name="ComfyUI_birefnet_ll",
            custom_node_url="https://github.com/lldacing/ComfyUI_birefnet_ll",
            workflow_id="image/background-remove",
            capability="background-remove",
            download_strategy="custom_node_auto",
        ),
    ],
    "image/image-upscale": [
        ModelSpec(
            id="realesrgan-x4plus",
            name="RealESRGAN x4plus",
            version="0.3.0",
            download_url="https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
            dest_subpath="models/upscale_models/RealESRGAN_x4plus.pth",
            size_mb=64,
            requires_hf_token=False,
            custom_node_name=None,
            custom_node_url=None,
            workflow_id="image/image-upscale",
            capability="image-upscale",
            download_strategy="direct_url",
        ),
    ],
}


# ── Result container ────────────────────────────────────────────────────────
class ModelResult:
    def __init__(self, spec: ModelSpec) -> None:
        self.spec = spec
        self.skipped: bool = False
        self.skip_reason: str = ""
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
        return not self.skipped and (self.already_installed or self.download_ok or (
            self.spec.download_strategy == "custom_node_auto" and self.custom_node_ok
        ))


# ── Helpers ─────────────────────────────────────────────────────────────────
def _log(msg: str) -> None:
    print(f"[ratec-install] {msg}", flush=True)


def _check_volume() -> tuple[bool, str]:
    if not VOLUME.exists():
        return False, f"não encontrado em {VOLUME}"
    if not VOLUME.is_dir():
        return False, f"{VOLUME} não é um diretório"
    try:
        probe = VOLUME / ".ratec_write_probe"
        probe.touch()
        probe.unlink()
    except OSError as exc:
        return False, f"sem permissão de escrita: {exc}"
    return True, str(VOLUME)


def _can_install(spec: ModelSpec, hf_token: str | None) -> tuple[bool, str]:
    """Verifica se o modelo pode ser instalado no ambiente atual."""
    if spec.requires_hf_token and not hf_token:
        return False, "requer HF_TOKEN (modelo comercial/privado no HuggingFace)"
    return True, ""


def _download(url: str, dest: Path, size_mb: int, token: str | None) -> tuple[bool, str, float]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    headers: dict[str, str] = {"User-Agent": "ratec-model-installer/2.0"}
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
                    print(f"\r  {downloaded / 1_000_000:.1f}MB / ~{size_mb}MB ({pct}%)", end="", flush=True)
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
        return False, f"workflow padrão não encontrado: {wf_path}"

    try:
        with open(wf_path) as fh:
            workflow = json.load(fh)
        if not workflow:
            return False, "workflow vazio"
    except json.JSONDecodeError as exc:
        return False, f"JSON inválido: {exc}"

    if spec.dest_subpath:
        model_dest = VOLUME / spec.dest_subpath
        if not model_dest.exists():
            return False, f"modelo não encontrado: {model_dest}"
        if model_dest.stat().st_size < 1_000:
            return False, f"arquivo suspeito — tamanho: {model_dest.stat().st_size} bytes"
    elif spec.custom_node_name:
        node_dir = COMFYUI / "custom_nodes" / spec.custom_node_name
        if not node_dir.exists():
            return False, f"custom node não encontrado: {node_dir}"

    return True, "OK"


def _try_install_model(spec: ModelSpec, hf_token: str | None) -> ModelResult:
    r = ModelResult(spec)

    # Verificar se pode ser instalado
    can, reason = _can_install(spec, hf_token)
    if not can:
        r.skipped = True
        r.skip_reason = reason
        _log(f"  PULADO: {reason}")
        return r

    # Verificar se arquivo já está instalado
    if spec.dest_subpath:
        dest = VOLUME / spec.dest_subpath
        if dest.exists() and dest.stat().st_size > 1_000:
            r.already_installed = True
            r.file_size_bytes = dest.stat().st_size
            _log(f"  Arquivo já instalado: {dest} ({r.file_size_bytes / 1_000_000:.1f}MB)")
        else:
            _log(f"  Baixando: {spec.download_url}")
            _log(f"  Destino: {dest}")
            ok, err, elapsed = _download(spec.download_url, dest, spec.size_mb, hf_token)
            r.download_ok = ok
            r.download_error = err
            r.download_time_s = elapsed
            if ok:
                r.file_size_bytes = dest.stat().st_size
                _log(f"  Download OK — {r.file_size_bytes / 1_000_000:.1f}MB em {elapsed:.1f}s")
            else:
                _log(f"  ERRO no download: {err}")
                if "403" in err:
                    _log("  DICA: configure HF_TOKEN para modelos privados/comerciais")
                return r

    # Instalar custom node
    if spec.custom_node_name and spec.custom_node_url:
        _log(f"  Custom node: {spec.custom_node_name}")
        ok, msg = _install_custom_node(spec.custom_node_name, spec.custom_node_url)
        r.custom_node_ok = ok
        r.custom_node_msg = msg
        _log(f"  Custom node: {'OK' if ok else 'ERRO'} — {msg}")
        if not ok and spec.download_strategy == "custom_node_auto":
            return r

    # Health check
    _log(f"  Health check: {spec.workflow_id}")
    ok, err = _workflow_health_check(spec)
    r.workflow_ok = ok
    r.workflow_error = err
    _log(f"  Health check: {'OK' if ok else f'FALHOU — {err}'}")

    return r


def _generate_report(
    volume_ok: bool,
    capability_results: dict[str, list[ModelResult]],
    active_models: dict[str, str],
    started_at: str,
) -> dict:
    capabilities = []
    for workflow_id, results in capability_results.items():
        active_id = active_models.get(workflow_id)
        tried = [
            {
                "id": r.spec.id,
                "name": r.spec.name,
                "version": r.spec.version,
                "status": (
                    "already_installed" if r.already_installed
                    else "installed" if r.installed
                    else "skipped" if r.skipped
                    else "failed"
                ),
                "active": r.spec.id == active_id,
                "skip_reason": r.skip_reason or None,
                "download_error": r.download_error or None,
                "download_time_s": round(r.download_time_s, 1) if r.download_ok else None,
                "custom_node": {
                    "name": r.spec.custom_node_name,
                    "status": "ok" if r.custom_node_ok else "failed",
                } if r.spec.custom_node_name else None,
                "health_check": "ok" if r.workflow_ok else f"failed: {r.workflow_error}",
            }
            for r in results
        ]
        capabilities.append({
            "workflow_id": workflow_id,
            "capability": results[0].spec.capability if results else workflow_id,
            "active_model": active_id,
            "models_tried": tried,
        })

    total_caps = len(capabilities)
    ready_caps = sum(1 for c in capabilities if c["active_model"])

    return {
        "ratec_ai_engine": "model-installation-report",
        "version": "2.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "started_at": started_at,
        "network_volume": {"path": str(VOLUME), "mounted": volume_ok},
        "capabilities": capabilities,
        "active_models": active_models,
        "summary": {
            "capabilities_total": total_caps,
            "capabilities_ready": ready_caps,
            "capabilities_failed": total_caps - ready_caps,
            "ready_for_playground": ready_caps == total_caps,
        },
    }


# ── Main ────────────────────────────────────────────────────────────────────
def main() -> int:
    started_at = datetime.now(timezone.utc).isoformat()
    hf_token = os.getenv("HF_TOKEN")

    _log("=" * 60)
    _log("RATEC AI ENGINE — Model Installation Manager v2.0")
    _log("=" * 60)
    _log(f"HF_TOKEN: {'configurado' if hf_token else 'NÃO configurado'}")
    if not hf_token:
        _log("  AVISO: sem HF_TOKEN, modelos comerciais serão pulados.")
        _log("  Configure: export HF_TOKEN=hf_xxx")

    # 1. Verificar Network Volume
    _log("")
    _log("Verificando Network Volume...")
    volume_ok, volume_msg = _check_volume()
    _log(f"  {'OK' if volume_ok else 'ERRO'}: {volume_msg}")

    capability_results: dict[str, list[ModelResult]] = {}
    active_models: dict[str, str] = {}

    for workflow_id, model_specs in CAPABILITY_PRIORITIES.items():
        capability = model_specs[0].capability if model_specs else workflow_id
        _log("")
        _log(f"╔══ Capability: {capability} ({workflow_id})")
        _log(f"║   {len(model_specs)} modelo(s) na lista de prioridade")

        results: list[ModelResult] = []
        capability_results[workflow_id] = results
        installed_model: str | None = None

        if not volume_ok:
            _log("║   PULADO — volume não disponível")
            for spec in model_specs:
                r = ModelResult(spec)
                r.skipped = True
                r.skip_reason = "Network Volume não disponível"
                results.append(r)
            continue

        for i, spec in enumerate(model_specs, 1):
            _log(f"║")
            _log(f"║  [{i}/{len(model_specs)}] {spec.name} (prioridade {i})")
            _log(f"║   Estratégia: {spec.download_strategy}")
            _log(f"║   Auth: {'HF_TOKEN necessário' if spec.requires_hf_token else 'não requer auth'}")

            r = _try_install_model(spec, hf_token)
            results.append(r)

            if r.installed:
                installed_model = spec.id
                active_models[workflow_id] = spec.id
                _log(f"║   ✓ Modelo ativo para '{capability}': {spec.name}")
                break
            else:
                _log(f"║   ✗ {spec.name} não disponível — tentando próxima alternativa")

        if not installed_model:
            _log(f"╚══ AVISO: nenhum modelo pôde ser instalado para '{capability}'")
        else:
            _log(f"╚══ OK: '{capability}' → {installed_model}")

    # 2. Escrever active_models.json
    if volume_ok and active_models:
        try:
            active_models_data = {
                **active_models,
                "_installed_at": datetime.now(timezone.utc).isoformat(),
            }
            active_path = VOLUME / "active_models.json"
            active_path.write_text(
                json.dumps(active_models_data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            _log(f"\nactive_models.json salvo: {active_path}")
        except Exception as exc:
            _log(f"\nAVISO: não foi possível salvar active_models.json: {exc}")

    # 3. Relatório
    report = _generate_report(volume_ok, capability_results, active_models, started_at)

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
    _log(f"Capabilities: {summary['capabilities_ready']}/{summary['capabilities_total']} prontas")

    if summary["ready_for_playground"]:
        _log("PRONTO — plataforma pronta para iniciar testes no AI Playground")
        return 0
    else:
        _log("ATENÇÃO — algumas capabilities não têm modelo instalado")
        _log("  Execute novamente com HF_TOKEN configurado para tentar modelos premium")
        return 1


if __name__ == "__main__":
    sys.exit(main())
