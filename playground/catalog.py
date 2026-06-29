"""
Leitor do catálogo de modelos do AI Lab.
Lê manifests YAML de runtime/models/catalog/.
"""
from __future__ import annotations

from pathlib import Path

import yaml

_CATALOG_ROOT = Path(__file__).parent.parent / "runtime" / "models" / "catalog"


def list_models() -> list[dict]:
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
