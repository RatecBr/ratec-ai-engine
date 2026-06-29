from __future__ import annotations

from typing import Any

from src.infrastructure.providers.comfyui.models import ComfyUIJobResult, ComfyUIOutputImage


class ComfyUIResultParser:
    """
    Converte a resposta bruta da API do ComfyUI para o formato interno do RATEC AI ENGINE.
    Isola o engine de qualquer detalhe da estrutura de output do ComfyUI.
    """

    def parse(
        self,
        history_entry: dict[str, Any],
        prompt_id: str,
        elapsed_ms: int = 0,
    ) -> ComfyUIJobResult:
        outputs = history_entry.get("outputs", {})
        return ComfyUIJobResult(
            prompt_id=prompt_id,
            outputs=outputs,
            images=self._extract_images(outputs),
            elapsed_ms=elapsed_ms,
        )

    def to_engine_output(self, result: ComfyUIJobResult) -> dict[str, Any]:
        """Converte ComfyUIJobResult para o dict de output padrão do RATEC AI ENGINE."""
        return {
            "prompt_id": result.prompt_id,
            "images": [
                {
                    "filename": img.filename,
                    "subfolder": img.subfolder,
                    "type": img.type,
                    "node_id": img.node_id,
                }
                for img in result.images
            ],
            "elapsed_ms": result.elapsed_ms,
        }

    def _extract_images(self, outputs: dict[str, Any]) -> list[ComfyUIOutputImage]:
        images: list[ComfyUIOutputImage] = []
        for node_id, node_output in outputs.items():
            for img in node_output.get("images", []):
                images.append(
                    ComfyUIOutputImage(
                        filename=img.get("filename", ""),
                        subfolder=img.get("subfolder", ""),
                        type=img.get("type", "output"),
                        node_id=node_id,
                    )
                )
        return images
