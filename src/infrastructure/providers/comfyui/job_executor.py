from __future__ import annotations

import asyncio
import copy
import time
from typing import Any

from src.infrastructure.providers.comfyui.client import ComfyUIClient
from src.infrastructure.providers.comfyui.exceptions import ComfyUIExecutionError, ComfyUITimeoutError
from src.infrastructure.providers.comfyui.result_parser import ComfyUIResultParser
from src.infrastructure.providers.comfyui.workflow_loader import ComfyUIWorkflowLoader


class ComfyUIJobExecutor:
    """
    Orquestra o ciclo completo de execução de um job no ComfyUI:
    carregar workflow → aplicar parâmetros → submeter → aguardar → parsear resultado.

    Toda a complexidade de comunicação com o ComfyUI permanece isolada aqui.
    """

    _POLL_INTERVAL: float = 2.0

    def __init__(
        self,
        client: ComfyUIClient,
        loader: ComfyUIWorkflowLoader,
        parser: ComfyUIResultParser,
    ) -> None:
        self._client = client
        self._loader = loader
        self._parser = parser

    async def execute(
        self,
        workflow_id: str,
        parameters: dict[str, Any],
        timeout: int = 300,
    ) -> dict[str, Any]:
        workflow = self._loader.load(workflow_id)
        workflow = self._apply_parameters(workflow, parameters)

        t_start = time.monotonic()
        response = await self._client.submit_prompt(workflow)

        if response.node_errors:
            raise ComfyUIExecutionError(
                f"Workflow '{workflow_id}' contém erros de node: {response.node_errors}"
            )

        history_entry = await self._poll_until_complete(response.prompt_id, timeout)
        elapsed_ms = int((time.monotonic() - t_start) * 1000)

        result = self._parser.parse(history_entry, response.prompt_id, elapsed_ms)
        return self._parser.to_engine_output(result)

    async def _poll_until_complete(self, prompt_id: str, timeout: int) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            history = await self._client.get_history(prompt_id)
            if prompt_id in history:
                return history[prompt_id]
            await asyncio.sleep(self._POLL_INTERVAL)

        raise ComfyUITimeoutError(
            f"Job '{prompt_id}' não completou dentro de {timeout}s"
        )

    def _apply_parameters(
        self, workflow: dict[str, Any], parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Aplica parâmetros ao workflow ComfyUI via sobrescrita de inputs por node.

        Formato esperado em parameters:
          {"node_overrides": {"<node_id>": {"<input_key>": <value>}}}

        Exemplo:
          {"node_overrides": {"6": {"text": "a photo of a cat"}, "3": {"seed": 42}}}
        """
        node_overrides: dict[str, dict[str, Any]] = parameters.get("node_overrides", {})
        if not node_overrides:
            return workflow

        workflow = copy.deepcopy(workflow)
        for node_id, inputs in node_overrides.items():
            if node_id in workflow and "inputs" in workflow[node_id]:
                workflow[node_id]["inputs"].update(inputs)

        return workflow
