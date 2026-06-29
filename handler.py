"""
RATEC AI ENGINE — RunPod Serverless Handler
Ponto de entrada do ambiente Serverless. Toda lógica está em runtime/.
"""
from __future__ import annotations

import runpod

from runtime import Runtime

_runtime = Runtime.initialize()


async def handler(job: dict) -> dict:
    return await _runtime.handle(job)


runpod.serverless.start({"handler": handler})
