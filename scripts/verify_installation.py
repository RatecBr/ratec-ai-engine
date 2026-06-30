#!/usr/bin/env python3
"""
RATEC AI ENGINE — Installation Verifier
Verifica o ambiente de execução. NUNCA altera o ambiente — apenas lê e reporta.

Uso:
  python scripts/verify_installation.py
  python scripts/verify_installation.py --no-report   (sem salvar arquivo)

Variáveis de ambiente:
  RUNPOD_VOLUME_PATH  — Network Volume (padrão: /runpod-volume)
  COMFYUI_PATH        — Instalação do ComfyUI (padrão: /comfyui)
  COMFYUI_URL         — URL do ComfyUI (padrão: http://127.0.0.1:8188)
  WORKFLOWS_DIR       — Diretório de workflows (padrão: {repo}/workflows)
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
from typing import Literal

# ── Paths ──────────────────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).parent.parent

VOLUME = Path(os.getenv("RUNPOD_VOLUME_PATH", "/runpod-volume"))
COMFYUI = Path(os.getenv("COMFYUI_PATH", "/comfyui"))
COMFYUI_URL = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")
WORKFLOWS_DIR = Path(os.getenv("WORKFLOWS_DIR", str(_REPO_ROOT / "workflows")))
CATALOG_DIR = _REPO_ROOT / "runtime" / "models" / "catalog"

# Diretórios obrigatórios no Network Volume
_REQUIRED_VOLUME_DIRS = [
    "models/BRIA",
    "models/checkpoints",
    "models/clip",
    "models/clip_vision",
    "models/controlnet",
    "models/ipadapter",
    "models/loras",
    "models/upscale_models",
    "models/vae",
    "output",
    "input",
    "temp",
    "logs",
]

# Workflows esperados (devem ter comfyui.json)
_EXPECTED_WORKFLOWS = [
    "image/identity",
    "image/background-remove",
    "image/image-upscale",
]

# Modelos e caminhos para verificação
_MODEL_CHECKS = [
    {
        "id": "bria-rmbg-1.4",
        "name": "BRIA RMBG-1.4",
        "type": "file",
        "path": VOLUME / "models/BRIA/RMBG-1.4.pth",
        "required": False,
        "min_size_mb": 100,
    },
    {
        "id": "birefnet",
        "name": "BiRefNet",
        "type": "custom_node",
        "path": COMFYUI / "custom_nodes/ComfyUI_birefnet_ll",
        "required": False,
        "min_size_mb": 0,
    },
    {
        "id": "realesrgan-x4plus",
        "name": "RealESRGAN x4plus",
        "type": "file",
        "path": VOLUME / "models/upscale_models/RealESRGAN_x4plus.pth",
        "required": False,
        "min_size_mb": 50,
    },
]

# ── Result types ───────────────────────────────────────────────────────────
Status = Literal["PASS", "WARNING", "FAIL"]


class Check:
    def __init__(self, name: str, status: Status, detail: str = "") -> None:
        self.name = name
        self.status = status
        self.detail = detail

    def __str__(self) -> str:
        icon = {"PASS": "✓", "WARNING": "⚠", "FAIL": "✗"}[self.status]
        detail = f" — {self.detail}" if self.detail else ""
        return f"[{self.status:7s}] {icon} {self.name}{detail}"


# ── Check functions ─────────────────────────────────────────────────────────
def check_volume() -> list[Check]:
    results = []

    # Volume exists
    if not VOLUME.exists():
        results.append(Check("Network Volume", "FAIL", f"não encontrado em {VOLUME}"))
        return results
    results.append(Check("Network Volume", "PASS", str(VOLUME)))

    # Write permission (probe without creating permanent file)
    probe = VOLUME / ".verify_probe"
    try:
        probe.touch()
        probe.unlink()
        results.append(Check("Permissão de escrita no volume", "PASS"))
    except OSError as exc:
        results.append(Check("Permissão de escrita no volume", "FAIL", str(exc)))

    # Required directories
    missing = [d for d in _REQUIRED_VOLUME_DIRS if not (VOLUME / d).exists()]
    if missing:
        results.append(Check(
            "Estrutura de diretórios no volume",
            "WARNING",
            f"{len(missing)} dir(s) ausentes: {', '.join(missing[:3])}{'...' if len(missing)>3 else ''}",
        ))
    else:
        results.append(Check("Estrutura de diretórios no volume", "PASS", f"{len(_REQUIRED_VOLUME_DIRS)} dirs OK"))

    # Disk space
    try:
        import shutil
        _, _, free = shutil.disk_usage(str(VOLUME))
        free_gb = free / 1_000_000_000
        status: Status = "PASS" if free_gb > 10 else ("WARNING" if free_gb > 2 else "FAIL")
        results.append(Check("Espaço em disco livre", status, f"{free_gb:.1f}GB disponíveis"))
    except Exception as exc:
        results.append(Check("Espaço em disco livre", "WARNING", f"não verificável: {exc}"))

    return results


def check_comfyui() -> list[Check]:
    results = []

    if not COMFYUI.exists():
        results.append(Check("ComfyUI instalação", "FAIL", f"não encontrado em {COMFYUI}"))
        return results
    results.append(Check("ComfyUI instalação", "PASS", str(COMFYUI)))

    # main.py
    main_py = COMFYUI / "main.py"
    if main_py.exists():
        results.append(Check("ComfyUI main.py", "PASS"))
    else:
        results.append(Check("ComfyUI main.py", "FAIL", f"não encontrado: {main_py}"))

    # custom_nodes dir
    cn_dir = COMFYUI / "custom_nodes"
    if cn_dir.exists():
        count = sum(1 for _ in cn_dir.iterdir() if _.is_dir())
        results.append(Check("ComfyUI custom_nodes", "PASS", f"{count} nós instalados"))
    else:
        results.append(Check("ComfyUI custom_nodes", "WARNING", "diretório não encontrado"))

    # HTTP health (only if running)
    try:
        req = urllib.request.Request(f"{COMFYUI_URL}/system_stats", headers={"User-Agent": "ratec-verifier/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        cuda = data.get("system", {}).get("cuda_device_type", "?")
        results.append(Check("ComfyUI HTTP /system_stats", "PASS", f"CUDA: {cuda}"))
    except Exception as exc:
        msg = str(exc)
        status = "WARNING" if "Connection refused" in msg or "timed out" in msg else "WARNING"
        results.append(Check("ComfyUI HTTP /system_stats", status, "não respondendo (pode não estar em execução)"))

    return results


def check_gpu() -> list[Check]:
    results = []
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10,
        )
        if out.returncode != 0:
            results.append(Check("GPU (nvidia-smi)", "FAIL", out.stderr.strip() or "exit code não-zero"))
            return results

        lines = [l.strip() for l in out.stdout.strip().splitlines() if l.strip()]
        if not lines:
            results.append(Check("GPU (nvidia-smi)", "FAIL", "nenhuma GPU detectada"))
            return results

        for line in lines:
            parts = [p.strip() for p in line.split(",")]
            name = parts[0] if parts else "?"
            vram = parts[1] if len(parts) > 1 else "?"
            driver = parts[2] if len(parts) > 2 else "?"
            results.append(Check("GPU detectada", "PASS", f"{name} | VRAM: {vram}MB | Driver: {driver}"))
    except FileNotFoundError:
        results.append(Check("GPU (nvidia-smi)", "FAIL", "nvidia-smi não encontrado"))
    except Exception as exc:
        results.append(Check("GPU (nvidia-smi)", "WARNING", str(exc)))

    # CUDA via Python
    try:
        out = subprocess.run(
            [sys.executable, "-c", "import torch; print(torch.version.cuda, torch.cuda.is_available())"],
            capture_output=True, text=True, timeout=15,
        )
        if out.returncode == 0:
            parts = out.stdout.strip().split()
            cuda_ver = parts[0] if parts else "?"
            available = parts[1] == "True" if len(parts) > 1 else False
            status = "PASS" if available else "WARNING"
            results.append(Check("CUDA (PyTorch)", status, f"versão {cuda_ver} | disponível: {available}"))
    except Exception:
        results.append(Check("CUDA (PyTorch)", "WARNING", "torch não disponível ou erro ao verificar"))

    return results


def check_runtime() -> list[Check]:
    results = []
    try:
        sys.path.insert(0, str(_REPO_ROOT))
        from runtime.configuration import RuntimeConfig
        config = RuntimeConfig.from_env()
        results.append(Check("Runtime (import)", "PASS", f"volume={config.volume_path}"))
    except Exception as exc:
        results.append(Check("Runtime (import)", "FAIL", str(exc)))
        return results

    try:
        from runtime.workflow import WorkflowManager
        wm = WorkflowManager(WORKFLOWS_DIR)
        available = wm.list_available()
        results.append(Check("WorkflowManager", "PASS", f"{len(available)} workflow(s): {available}"))
    except Exception as exc:
        results.append(Check("WorkflowManager", "FAIL", str(exc)))

    return results


def check_models() -> list[Check]:
    results = []
    for m in _MODEL_CHECKS:
        path: Path = m["path"]
        name = m["name"]

        if m["type"] == "file":
            if path.exists():
                size_mb = path.stat().st_size / 1_000_000
                if m["min_size_mb"] and size_mb < m["min_size_mb"]:
                    results.append(Check(f"Modelo {name}", "WARNING", f"arquivo suspeito: {size_mb:.1f}MB (esperado ≥{m['min_size_mb']}MB)"))
                else:
                    results.append(Check(f"Modelo {name}", "PASS", f"{size_mb:.1f}MB em {path}"))
            else:
                status: Status = "WARNING" if not m["required"] else "FAIL"
                results.append(Check(f"Modelo {name}", status, f"não instalado em {path}"))

        elif m["type"] == "custom_node":
            if path.exists():
                results.append(Check(f"Custom node {name}", "PASS", str(path)))
            else:
                status = "WARNING" if not m["required"] else "FAIL"
                results.append(Check(f"Custom node {name}", status, f"não instalado em {path}"))

    return results


def check_workflows() -> list[Check]:
    results = []

    if not WORKFLOWS_DIR.exists():
        results.append(Check("Diretório de workflows", "FAIL", f"não encontrado: {WORKFLOWS_DIR}"))
        return results
    results.append(Check("Diretório de workflows", "PASS", str(WORKFLOWS_DIR)))

    for wf_id in _EXPECTED_WORKFLOWS:
        comfyui_path = WORKFLOWS_DIR / wf_id / "comfyui.json"
        manifest_path = WORKFLOWS_DIR / wf_id / "manifest.yaml"

        if not comfyui_path.exists():
            results.append(Check(f"Workflow {wf_id}", "FAIL", "comfyui.json não encontrado"))
            continue

        try:
            with open(comfyui_path) as f:
                wf = json.load(f)
            node_count = len(wf)
            results.append(Check(f"Workflow {wf_id}", "PASS", f"JSON válido, {node_count} nós"))
        except Exception as exc:
            results.append(Check(f"Workflow {wf_id}", "FAIL", f"JSON inválido: {exc}"))

        # Check model variant files
        wf_dir = WORKFLOWS_DIR / wf_id
        variants = [p.name for p in wf_dir.glob("comfyui.*.json")]
        if variants:
            results.append(Check(f"Workflow {wf_id} — variantes", "PASS", ", ".join(variants)))

    return results


def check_active_models() -> list[Check]:
    results = []
    active_path = VOLUME / "active_models.json"

    if not active_path.exists():
        results.append(Check("active_models.json", "WARNING", "não encontrado — execute install_models.py"))
        return results

    try:
        with open(active_path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        results.append(Check("active_models.json", "FAIL", f"JSON inválido: {exc}"))
        return results

    installed_at = data.get("_installed_at", "?")
    results.append(Check("active_models.json", "PASS", f"instalado em {installed_at}"))

    for key, value in data.items():
        if key.startswith("_"):
            continue
        if isinstance(value, dict):
            active = value.get("active", "?")
            status_val = value.get("status", "?")
            st: Status = "PASS" if status_val == "ready" else "WARNING"
            results.append(Check(f"  Capability {key}", st, f"modelo ativo: {active} | status: {status_val}"))
        elif isinstance(value, str):
            results.append(Check(f"  Capability/Workflow {key}", "PASS", f"modelo: {value}"))

    return results


def check_catalog() -> list[Check]:
    results = []

    if not CATALOG_DIR.exists():
        results.append(Check("Catálogo de modelos", "FAIL", f"não encontrado: {CATALOG_DIR}"))
        return results

    manifests = list(CATALOG_DIR.rglob("manifest.yaml"))
    results.append(Check("Catálogo de modelos", "PASS", f"{len(manifests)} manifest(s) encontrados"))

    try:
        import yaml  # optional dependency
        for mp in manifests:
            try:
                with open(mp, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                model_id = data.get("id", mp.parent.name)
                status_val = data.get("status", "?")
                results.append(Check(f"  Manifest {model_id}", "PASS", f"status: {status_val}"))
            except Exception as exc:
                results.append(Check(f"  Manifest {mp.parent.name}", "FAIL", str(exc)))
    except ImportError:
        results.append(Check("Catálogo (parse YAML)", "WARNING", "pyyaml não disponível — apenas contagem verificada"))

    return results


# ── Report generation ───────────────────────────────────────────────────────
def generate_markdown_report(
    sections: dict[str, list[Check]],
    overall: Status,
    generated_at: str,
) -> str:
    lines = [
        "# RATEC AI ENGINE — Validation Report",
        f"",
        f"**Gerado em:** {generated_at}  ",
        f"**Status geral:** {overall}  ",
        f"**Volume:** {VOLUME}  ",
        f"**ComfyUI:** {COMFYUI}  ",
        f"",
    ]

    summary_pass = 0
    summary_warn = 0
    summary_fail = 0

    for section_name, checks in sections.items():
        lines.append(f"## {section_name}")
        lines.append("")
        lines.append("| Check | Status | Detalhes |")
        lines.append("|-------|--------|---------|")
        for c in checks:
            icon = {"PASS": "✅", "WARNING": "⚠️", "FAIL": "❌"}[c.status]
            lines.append(f"| {c.name} | {icon} {c.status} | {c.detail} |")
            if c.status == "PASS":
                summary_pass += 1
            elif c.status == "WARNING":
                summary_warn += 1
            else:
                summary_fail += 1
        lines.append("")

    lines += [
        "## Resumo",
        "",
        f"| Total | PASS | WARNING | FAIL |",
        f"|-------|------|---------|------|",
        f"| {summary_pass+summary_warn+summary_fail} | {summary_pass} | {summary_warn} | {summary_fail} |",
        "",
        f"**Status final: {overall}**",
    ]

    return "\n".join(lines)


# ── Main ────────────────────────────────────────────────────────────────────
def main() -> int:
    save_report = "--no-report" not in sys.argv
    generated_at = datetime.now(timezone.utc).isoformat()

    print("=" * 65)
    print("RATEC AI ENGINE — Installation Verifier")
    print("=" * 65)
    print()

    sections: dict[str, list[Check]] = {
        "Network Volume": check_volume(),
        "ComfyUI": check_comfyui(),
        "GPU / CUDA": check_gpu(),
        "Runtime": check_runtime(),
        "Modelos": check_models(),
        "Workflows": check_workflows(),
        "Active Models": check_active_models(),
        "Catálogo": check_catalog(),
    }

    total = pass_count = warn_count = fail_count = 0
    for section_name, checks in sections.items():
        print(f"── {section_name} ──")
        for c in checks:
            print(f"  {c}")
            if c.status == "PASS":
                pass_count += 1
            elif c.status == "WARNING":
                warn_count += 1
            else:
                fail_count += 1
            total += 1
        print()

    overall: Status = "PASS" if fail_count == 0 and warn_count == 0 else (
        "FAIL" if fail_count > 0 else "WARNING"
    )

    print("=" * 65)
    print(f"Total: {total} | PASS: {pass_count} | WARNING: {warn_count} | FAIL: {fail_count}")
    print(f"Status: {overall}")
    print("=" * 65)

    if save_report:
        report_md = generate_markdown_report(sections, overall, generated_at)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = VOLUME / "logs" / f"runtime_validation_report_{ts}.md"
        try:
            (VOLUME / "logs").mkdir(parents=True, exist_ok=True)
            report_path.write_text(report_md, encoding="utf-8")
            print(f"\nRelatório salvo: {report_path}")
        except Exception as exc:
            print(f"\nAVISO: não foi possível salvar o relatório: {exc}")

    return 0 if overall != "FAIL" else 1


if __name__ == "__main__":
    sys.exit(main())
