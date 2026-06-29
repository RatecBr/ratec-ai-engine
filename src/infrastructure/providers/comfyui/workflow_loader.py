from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.infrastructure.providers.comfyui.exceptions import ComfyUIWorkflowNotFoundError


class ComfyUIWorkflowLoader:
    """
    Localiza e carrega workflows ComfyUI (formato API JSON) do diretório workflows/.

    Convenção de arquivo: workflows/{workflow_id}/comfyui.json
    O formato API do ComfyUI é distinto do formato de interface — é o JSON
    exportado via "Save (API Format)" no ComfyUI com o modo dev ativado.
    """

    _FILENAME = "comfyui.json"

    def __init__(self, workflows_root: Path) -> None:
        self._root = workflows_root

    def load(self, workflow_id: str) -> dict[str, Any]:
        """Carrega o workflow JSON do ComfyUI para o workflow_id fornecido."""
        path = self._path_for(workflow_id)
        if not path.exists():
            raise ComfyUIWorkflowNotFoundError(
                f"Workflow ComfyUI não encontrado: '{workflow_id}'. "
                f"Esperado em: {path}"
            )
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def exists(self, workflow_id: str) -> bool:
        return self._path_for(workflow_id).exists()

    def list_available(self) -> list[str]:
        """Retorna IDs de todos os workflows ComfyUI disponíveis no diretório."""
        return [p.parent.name for p in self._root.rglob(self._FILENAME)]

    def _path_for(self, workflow_id: str) -> Path:
        return self._root / workflow_id / self._FILENAME
