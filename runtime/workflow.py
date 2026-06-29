from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


class WorkflowManager:
    """
    Localiza, carrega e parametriza workflows ComfyUI do diretório workflows/.
    Convenção: workflows/{workflow_id}/comfyui.json
    """

    _COMFYUI_FILENAME = "comfyui.json"

    def __init__(self, workflows_dir: Path) -> None:
        self._root = workflows_dir

    def load_comfyui(self, workflow_id: str) -> dict[str, Any]:
        path = self._path_for(workflow_id)
        if not path.exists():
            raise FileNotFoundError(
                f"Workflow ComfyUI não encontrado: '{workflow_id}'. Esperado em: {path}"
            )
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def exists(self, workflow_id: str) -> bool:
        return self._path_for(workflow_id).exists()

    def list_available(self) -> list[str]:
        """Retorna IDs de todos os workflows ComfyUI disponíveis."""
        return sorted(
            str(p.parent.relative_to(self._root))
            for p in self._root.rglob(self._COMFYUI_FILENAME)
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

    def _path_for(self, workflow_id: str) -> Path:
        return self._root / workflow_id / self._COMFYUI_FILENAME
