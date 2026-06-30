from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


class WorkflowManager:
    """
    Localiza, carrega e parametriza workflows ComfyUI do diretório workflows/.

    Convenção de arquivos:
      workflows/{workflow_id}/comfyui.json           — workflow padrão (primeiro modelo disponível)
      workflows/{workflow_id}/comfyui.{model_id}.json — variante específica por modelo
    """

    _DEFAULT_FILENAME = "comfyui.json"

    def __init__(self, workflows_dir: Path) -> None:
        self._root = workflows_dir

    def load_comfyui(self, workflow_id: str, model_id: str | None = None) -> dict[str, Any]:
        """
        Carrega o workflow ComfyUI para o workflow_id dado.

        Se model_id for fornecido e existir comfyui.{model_id}.json, usa esse arquivo.
        Caso contrário, usa o comfyui.json padrão (fallback).
        """
        if model_id:
            model_path = self._root / workflow_id / f"comfyui.{model_id}.json"
            if model_path.exists():
                with model_path.open("r", encoding="utf-8") as f:
                    return json.load(f)

        path = self._root / workflow_id / self._DEFAULT_FILENAME
        if not path.exists():
            raise FileNotFoundError(
                f"Workflow ComfyUI não encontrado: '{workflow_id}'. Esperado em: {path}"
            )
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def exists(self, workflow_id: str) -> bool:
        return (self._root / workflow_id / self._DEFAULT_FILENAME).exists()

    def list_available(self) -> list[str]:
        """Retorna IDs de todos os workflows ComfyUI disponíveis (que têm comfyui.json)."""
        return sorted(
            str(p.parent.relative_to(self._root))
            for p in self._root.rglob(self._DEFAULT_FILENAME)
        )

    def list_model_variants(self, workflow_id: str) -> list[str]:
        """Retorna IDs de modelos com arquivo de workflow dedicado (comfyui.{model_id}.json)."""
        wf_dir = self._root / workflow_id
        if not wf_dir.exists():
            return []
        prefix = "comfyui."
        return sorted(
            p.stem[len(prefix):]
            for p in wf_dir.glob(f"{prefix}*.json")
            if p.stem != "comfyui"
        )

    def apply_node_overrides(
        self,
        workflow: dict[str, Any],
        node_overrides: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Aplica sobrescrita de inputs por node ao workflow.
        node_overrides: {"<node_id>": {"<input_key>": <value>}}
        """
        if not node_overrides:
            return workflow
        workflow = copy.deepcopy(workflow)
        for node_id, inputs in node_overrides.items():
            if node_id in workflow and "inputs" in workflow[node_id]:
                workflow[node_id]["inputs"].update(inputs)
        return workflow
