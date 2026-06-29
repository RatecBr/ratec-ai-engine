"""
AI Lab — Cache experimental de resultados.
Evita re-execuções para o mesmo workflow + parâmetros + imagem.
"""
from __future__ import annotations

import hashlib
import json


def compute_key(workflow_id: str, input_hash: str | None, node_overrides: dict) -> str:
    """SHA-256 de (workflow_id + input_hash + node_overrides ordenado)."""
    payload = json.dumps(
        {"w": workflow_id, "h": input_hash or "", "o": node_overrides},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:32]
