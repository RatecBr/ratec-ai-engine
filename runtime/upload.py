from __future__ import annotations

import time

import httpx

from runtime.configuration import RuntimeConfig


async def upload_image(
    client: httpx.AsyncClient,
    config: RuntimeConfig,
    image_data: bytes,
    filename: str = "input.png",
    image_type: str = "input",
) -> tuple[str, int]:
    """
    Faz upload de uma imagem para o ComfyUI.
    Retorna (nome_no_servidor, elapsed_ms).
    """
    t0 = time.monotonic()
    r = await client.post(
        f"{config.comfyui_url}/upload/image",
        files={"image": (filename, image_data, "image/png")},
        data={"type": image_type},
        timeout=30,
    )
    r.raise_for_status()
    elapsed_ms = int((time.monotonic() - t0) * 1000)
    return r.json()["name"], elapsed_ms
