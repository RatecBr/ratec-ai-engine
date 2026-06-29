from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from src.domain.entities.workflow_manifest import ManifestRequirements, WorkflowManifest

_REQUIRED_MANIFEST_FIELDS = ("id", "version", "name", "provider", "pipeline")
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
_VRAM_RE = re.compile(r"^(\d+(?:\.\d+)?)\s*(MB|GB)$", re.IGNORECASE)


def _parse_vram_mb(value: str) -> int | None:
    """Converte string de VRAM (ex: '24GB', '512MB') para MB."""
    if not value:
        return None
    m = _VRAM_RE.match(value.strip())
    if not m:
        return None
    amount, unit = float(m.group(1)), m.group(2).upper()
    return int(amount * 1024) if unit == "GB" else int(amount)


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
    - campos obrigatórios e formatos do manifest
    - versão no formato semver (x.y.z)
    - existência e validade do comfyui.json (provider=comfyui)
    - presença de class_type em todos os nodes
    - compatibilidade com providers disponíveis
    - requisitos mínimos do Runtime (VRAM, GPU)
    """

    def __init__(self, workflows_root: Path) -> None:
        self._root = workflows_root

    # ── API pública ───────────────────────────────────────────────────────────

    def validate(self, manifest: WorkflowManifest) -> ValidationResult:
        """Validação completa do manifest e arquivos associados."""
        errors: list[str] = []
        warnings: list[str] = []

        self._check_required_fields(manifest, errors)
        self._check_version_format(manifest, warnings)
        self._check_workflow_directory(manifest, warnings)

        if manifest.provider == "comfyui":
            self._check_comfyui_json(manifest, errors, warnings)

        return ValidationResult(
            valid=len(errors) == 0,
            workflow_id=manifest.id,
            errors=errors,
            warnings=warnings,
        )

    def validate_runtime_compatibility(
        self,
        manifest: WorkflowManifest,
        available_providers: list[str] | None = None,
        available_vram_mb: int | None = None,
    ) -> ValidationResult:
        """
        Valida compatibilidade do workflow com o estado atual do Runtime.
        Complementa validate() com verificações de runtime ao vivo.
        """
        base = self.validate(manifest)
        extra_errors: list[str] = []
        extra_warnings: list[str] = []

        # Provider disponível?
        if available_providers and manifest.provider:
            if manifest.provider not in available_providers and manifest.provider != "local":
                extra_errors.append(
                    f"provider '{manifest.provider}' não está disponível. "
                    f"Disponíveis: {available_providers}"
                )

        # VRAM suficiente?
        if available_vram_mb is not None:
            req = manifest.requirements
            if isinstance(req, ManifestRequirements) and req.min_vram:
                required_mb = _parse_vram_mb(req.min_vram)
                if required_mb and available_vram_mb < required_mb:
                    extra_errors.append(
                        f"VRAM insuficiente: workflow requer {req.min_vram}, "
                        f"disponível {available_vram_mb} MB"
                    )

        # GPU obrigatória?
        if manifest.requirements.gpu and available_vram_mb is None:
            extra_warnings.append("workflow requer GPU mas nenhuma GPU foi detectada")

        return ValidationResult(
            valid=base.valid and len(extra_errors) == 0,
            workflow_id=manifest.id,
            errors=base.errors + extra_errors,
            warnings=base.warnings + extra_warnings,
        )

    def validate_or_raise(self, manifest: WorkflowManifest) -> None:
        result = self.validate(manifest)
        if not result.valid:
            raise ValueError(
                f"Workflow '{manifest.id}' falhou na validação:\n" +
                "\n".join(f"  - {e}" for e in result.errors)
            )

    # ── Checks internos ───────────────────────────────────────────────────────

    def _check_required_fields(self, manifest: WorkflowManifest, errors: list[str]) -> None:
        for field_name in _REQUIRED_MANIFEST_FIELDS:
            if not getattr(manifest, field_name, None):
                errors.append(f"campo obrigatório ausente no manifest: '{field_name}'")

    def _check_version_format(self, manifest: WorkflowManifest, warnings: list[str]) -> None:
        if manifest.version and not _SEMVER_RE.match(manifest.version):
            warnings.append(
                f"versão '{manifest.version}' não segue o formato semver (x.y.z)"
            )

    def _check_workflow_directory(self, manifest: WorkflowManifest, warnings: list[str]) -> None:
        if not (self._root / manifest.id).exists():
            warnings.append(f"diretório do workflow não encontrado: {self._root / manifest.id}")

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

        nodes_without_class = [
            node_id for node_id, node in workflow.items()
            if isinstance(node, dict) and not node.get("class_type")
        ]
        if nodes_without_class:
            warnings.append(
                f"nodes sem 'class_type' em comfyui.json: {nodes_without_class}"
            )
