from __future__ import annotations

from src.domain.entities.workflow import Workflow
from src.domain.entities.workflow_manifest import WorkflowManifest
from src.domain.interfaces.workflow_registry import IWorkflowRegistry


class WorkflowRegistry(IWorkflowRegistry):
    def __init__(self) -> None:
        self._workflows: dict[str, Workflow] = {}
        self._manifests: dict[str, WorkflowManifest] = {}

    def register(self, workflow: Workflow) -> None:
        self._workflows[workflow.id] = workflow

    def register_from_manifest(self, manifest: WorkflowManifest, workflow: Workflow) -> None:
        """Registra um workflow associando-o ao seu manifesto de metadados."""
        self._manifests[manifest.id] = manifest
        self.register(workflow)

    def get(self, workflow_id: str) -> Workflow | None:
        return self._workflows.get(workflow_id)

    def get_manifest(self, workflow_id: str) -> WorkflowManifest | None:
        """Retorna o manifesto associado ao workflow, se disponível."""
        return self._manifests.get(workflow_id)

    def list_all(self) -> list[Workflow]:
        return list(self._workflows.values())

    def list_manifests(self) -> list[WorkflowManifest]:
        """Lista todos os manifestos registrados."""
        return list(self._manifests.values())
