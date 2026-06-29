from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from src.domain.entities.workflow_manifest import WorkflowManifest

_COMFYUI_REQUIRED_NODES = {"LoadImage", "SaveImage"}
_REQUIRED_MANIFEST_FIELDS = ("id", "version", "name", "provider", "pipeline")


@dataclass
class ValidationResult:
    valid: bool
    workflow_id: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        status = "OK" if self.valid else "FALHOU"
        lines = [f"[{status}] {self.workflow_id}"]
        for e in self.errors:
            lines.append(f"  ERRO: {e}")
        for w in self.warnings:
            lines.append(f"  AVISO: {w}")
        return "\n".join(lines)


class WorkflowValidator:
    """
    Valida workflows antes da execução.
    Nenhum Workflow deverá ser executado sem passar por essa validação.

    Verifica:
    - campos obrigatórios no manifest
    - existência do comfyui.json (para provider=comfyui)
    - JSON válido no comfyui.json
    - nodes obrigatórios para o workflow identity
    """

    def __init__(self, workflows_root: Path) -> None:
        self._root = workflows_root

    def validate(self, manifest: WorkflowManifest) -> ValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        self._check_required_fields(manifest, errors)
        self._check_workflow_directory(manifest, warnings)

        if manifest.provider == "comfyui":
            self._check_comfyui_json(manifest, errors, warnings)

        return ValidationResult(
            valid=len(errors) == 0,
            workflow_id=manifest.id,
            errors=errors,
            warnings=warnings,
        )

    def validate_or_raise(self, manifest: WorkflowManifest) -> None:
        result = self.validate(manifest)
        if not result.valid:
            raise ValueError(
                f"Workflow '{manifest.id}' falhou na validação:\n" +
                "\n".join(f"  - {e}" for e in result.errors)
            )

    # ── Checks ────────────────────────────────────────────────────────────────

    def _check_required_fields(self, manifest: WorkflowManifest, errors: list[str]) -> None:
        for field_name in _REQUIRED_MANIFEST_FIELDS:
            if not getattr(manifest, field_name, None):
                errors.append(f"campo obrigatório ausente no manifest: '{field_name}'")

    def _check_workflow_directory(self, manifest: WorkflowManifest, warnings: list[str]) -> None:
        workflow_dir = self._root / manifest.id
        if not workflow_dir.exists():
            warnings.append(f"diretório do workflow não encontrado: {workflow_dir}")

    def _check_comfyui_json(
        self,
        manifest: WorkflowManifest,
        errors: list[str],
        warnings: list[str],
    ) -> None:
        path = self._root / manifest.id / "comfyui.json"

        if not path.exists():
            errors.append(f"comfyui.json não encontrado: {path}")
            return

        try:
            with path.open("r", encoding="utf-8") as f:
                workflow = json.load(f)
        except json.JSONDecodeError as exc:
            errors.append(f"comfyui.json contém JSON inválido: {exc}")
            return

        if not isinstance(workflow, dict) or not workflow:
            errors.append("comfyui.json deve ser um objeto JSON não-vazio")
            return

        class_types = {
            node.get("class_type")
            for node in workflow.values()
            if isinstance(node, dict)
        }
        if not class_types:
            warnings.append("comfyui.json não contém nenhum node com 'class_type'")
