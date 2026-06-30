"""
Leitor do catálogo de modelos do AI Lab.
Lê manifests YAML de runtime/models/catalog/.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import yaml

_CATALOG_ROOT = Path(__file__).parent.parent / "runtime" / "models" / "catalog"
_WORKFLOWS_DIR = Path(__file__).parent.parent / "workflows"


def list_models() -> list[dict]:
    """Retorna todos os modelos do catálogo com campos enriquecidos."""
    models = []
    for p in sorted(_CATALOG_ROOT.rglob("manifest.yaml")):
        try:
            with open(p, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            data["_catalog_id"] = p.parent.name
            models.append(data)
        except Exception as exc:
            models.append({"_catalog_id": p.parent.name, "_error": str(exc)})
    return models


def list_capability_models(volume_path: str | None = None) -> list[dict]:
    """
    Retorna por capability: lista de modelos compatíveis com prioridade,
    modelo atualmente ativo, requisitos de autenticação e licença.
    """
    # Ler active_models.json do volume
    active_models: dict[str, str] = {}
    _volume = Path(volume_path or os.getenv("RUNPOD_VOLUME_PATH", "/runpod-volume"))
    active_path = _volume / "active_models.json"
    try:
        with open(active_path, encoding="utf-8") as f:
            data = json.load(f)
        active_models = {k: v for k, v in data.items() if not k.startswith("_")}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass

    # Agrupar modelos por capability
    all_models = list_models()
    capability_map: dict[str, list[dict]] = {}
    for m in all_models:
        if "_error" in m:
            continue
        for cap in m.get("capabilities", []):
            capability_map.setdefault(cap, []).append(m)

    result = []
    for capability, models in sorted(capability_map.items()):
        # Determinar workflow_id para esta capability
        workflow_id = next(
            (wf for m in models for wf in m.get("compatible_workflows", [])
             if wf.endswith(capability) or wf.endswith(capability.replace("-", "_"))),
            None,
        )

        # Ordenar por fallback_priority
        sorted_models = sorted(models, key=lambda m: m.get("fallback_priority", 99))

        active_model_id = active_models.get(workflow_id) if workflow_id else None

        # Verificar se existe arquivo de workflow instalado no volume
        model_list = []
        for m in sorted_models:
            model_id = m.get("id", m.get("_catalog_id", ""))
            is_active = model_id == active_model_id

            # Verificar se o modelo está instalado (arquivo no volume)
            install_path = m.get("installation", {}).get("volume_path", "")
            is_installed = False
            if install_path:
                install_dir = Path(install_path)
                is_installed = install_dir.exists() and any(install_dir.iterdir())
            elif is_active:
                is_installed = True  # custom_node_auto: assume instalado se ativo

            model_list.append({
                "id": model_id,
                "name": m.get("name", model_id),
                "version": m.get("version"),
                "vendor": m.get("vendor"),
                "license_type": m.get("license_type") or m.get("license"),
                "preferred": m.get("preferred", False),
                "fallback_priority": m.get("fallback_priority", 99),
                "requires_hf_token": m.get("requires_hf_token", False),
                "requires_license_acceptance": m.get("requires_license_acceptance", False),
                "download_strategy": m.get("download_strategy", "unknown"),
                "status": m.get("status", "unknown"),
                "is_active": is_active,
                "is_installed": is_installed,
                "min_vram": m.get("requirements", {}).get("min_vram"),
                "size_mb": m.get("metrics", {}).get("model_size_mb"),
                "workflow_variants": m.get("workflow_variants", []),
            })

        result.append({
            "capability": capability,
            "workflow_id": workflow_id,
            "active_model": active_model_id,
            "models": model_list,
        })

    return result
