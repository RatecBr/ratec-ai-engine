"""
RATEC AI ENGINE — RunPod Serverless Handler
Ponto de entrada do ambiente Serverless.
"""
from __future__ import annotations

import runpod
import asyncio
import httpx
import urllib.parse
from runtime import Runtime
from src.main import app

_runtime = Runtime.initialize()


async def handler(job: dict) -> dict:
    """
    Handler assíncrono do RunPod.
    Ele processa tanto execuções legadas (apenas workflow_id)
    quanto requisições de Gateway REST (http_path).
    """
    job_input = job.get("input", {})
    
    # 1. Se for uma requisição do Gateway da Vercel (API Route /api/[...path])
    if "http_path" in job_input:
        method = job_input.get("http_method", "GET")
        path = job_input.get("http_path", "/")
        query = job_input.get("http_query", {})
        body = job_input.get("http_body")
        
        # Reconstrói a query string se necessário
        query_string = urllib.parse.urlencode(query) if query else ""
        url = f"http://testserver{path}"
        if query_string:
            url += f"?{query_string}"

        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
            request_kwargs = {}
            if body is not None:
                request_kwargs["json"] = body
                
            response = await client.request(method, url, **request_kwargs)
            return response.json()
            
    # 2. Execução legada / worker direto
    return await _runtime.handle(job)


runpod.serverless.start({"handler": handler})
