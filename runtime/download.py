from __future__ import annotations

import base64
import time

import httpx

from runtime.configuration import RuntimeConfig


async def download_image(
    client: httpx.AsyncClient,
    config: RuntimeConfig,
    filename: str,
    subfolder: str = "",
    file_type: str = "output",
) -> tuple[str, int]:
    """
    Baixa uma imagem do output do ComfyUI.
    Retorna (base64_string, elapsed_ms).
    """
    t0 = time.monotonic()
    r = await client.get(
        f"{config.comfyui_url}/view",
        params={"filename": filename, "subfolder": subfolder, "type": file_type},
        timeout=30,
    )
    r.raise_for_status()
    elapsed_ms = int((time.monotonic() - t0) * 1000)
    return base64.b64encode(r.content).decode("utf-8"), elapsed_ms
