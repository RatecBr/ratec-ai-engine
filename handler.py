"""
RATEC AI ENGINE — RunPod Serverless Handler
Ponto de entrada do ambiente Serverless.
"""
import runpod
from runtime import Runtime
from src.application.admin.version_provider import version_provider

_runtime = Runtime.initialize()

try:
    info = version_provider.build_info
    print("=" * 40, flush=True)
    print("RATEC AI ENGINE", flush=True)
    print(f"Version: {info.get('engine_version')}", flush=True)
    print(f"Commit: {info.get('git_short_commit')}", flush=True)
    print(f"Branch: {info.get('git_branch')}", flush=True)
    print(f"Docker: {info.get('docker_tag')}", flush=True)
    print(f"Build: {info.get('build_date')}", flush=True)
    print(f"Started: {_runtime.boot_time.isoformat()}", flush=True)
    print("=" * 40, flush=True)
except Exception as e:
    print(f"Failed to print startup banner: {e}", flush=True)


async def handler(job: dict) -> dict:
    """
    Handler assíncrono do RunPod.
    Processa execuções de IA (workflow_id) e requisições do Console Web (http_path)
    sem carregar FastAPI para manter o container leve.
    """
    job_input = job.get("input", {})

    if "http_path" in job_input:
        path = job_input.get("http_path", "/")
        try:
            if path == "/admin/version":
                gpu_model = "unknown"
                try:
                    from runtime.observability import get_gpu
                    gpu_model = get_gpu().model
                except Exception:
                    pass
                return {
                    "success": True,
                    "data": version_provider.get_version_info(
                        boot_time=_runtime.boot_time,
                        gpu_model=gpu_model,
                    ),
                }

            elif path == "/admin/health":
                from src.application.admin import health_service
                return {"success": True, "data": health_service.get_platform_health()}

            elif path == "/admin/runtime":
                from src.application.admin import runtime_service
                return {"success": True, "data": runtime_service.get_runtime_info()}

            elif path == "/admin/gpu":
                from src.application.admin import gpu_service
                return {"success": True, "data": gpu_service.get_gpu_telemetry()}

            elif path == "/admin/storage":
                from src.application.admin import storage_service
                return {"success": True, "data": storage_service.get_storage_info()}

            elif path == "/admin/logs":
                from src.application.admin import logs_service
                return {"success": True, "data": logs_service.get_platform_logs("all")}

            elif path == "/admin/metrics":
                from src.application.admin import metrics_service
                return {"success": True, "data": metrics_service.get_system_metrics()}

            elif path == "/admin/models":
                from src.application.admin import models_service
                return {"success": True, "data": models_service.get_installed_models()}

            elif path == "/admin/workflows":
                from src.application.admin import workflows_service
                return {"success": True, "data": workflows_service.get_registered_workflows()}

            elif path == "/admin/system":
                from src.application.admin import (
                    system_service, gpu_service, runtime_service, storage_service,
                )
                data = system_service.get_system_info()
                data["gpu"] = gpu_service.get_gpu_telemetry()
                data["runtime"] = runtime_service.get_runtime_info()
                data["storage"] = storage_service.get_storage_info()
                data["comfyui_manager"] = data["runtime"]["comfyui_manager"]
                return {"success": True, "data": data}

            # ── Rotas públicas /v1/* (Console Web) ──────────────────────────────

            elif path == "/v1/health":
                from src.application.admin import health_service
                return health_service.get_platform_health()

            elif path == "/v1/capabilities":
                from runtime import _CAPABILITY_ROUTES
                return {
                    "status": "ok",
                    "capabilities": sorted(_CAPABILITY_ROUTES.keys()),
                    "total": len(_CAPABILITY_ROUTES),
                }

            elif path == "/v1/workflows":
                available = _runtime._wm.list_available()
                workflows = [
                    {
                        "id": wf_id,
                        "name": wf_id.split("/")[-1].replace("-", " ").title(),
                        "version": "1.0",
                        "description": f"Workflow de IA: {wf_id}",
                    }
                    for wf_id in available
                ]
                return {"status": "ok", "workflows": workflows, "total": len(workflows)}

            elif path == "/v1/models":
                model_list = [
                    {"id": model_id, "name": model_id, "workflow": wf_id, "status": "available"}
                    for wf_id, model_id in _runtime._active_models.items()
                ]
                return {"status": "ok", "models": model_list, "total": len(model_list)}

            elif path == "/v1/jobs":
                method = job_input.get("http_method", "GET").upper()
                if method == "POST":
                    import json as _json
                    import uuid as _uuid
                    body = job_input.get("http_body", {})
                    if isinstance(body, str):
                        body = _json.loads(body)
                    job_id = str(_uuid.uuid4())[:8]
                    result = await _runtime.handle({
                        "input": {
                            "workflow_id": body.get("workflow_id"),
                            "input": body.get("input", {}),
                        }
                    })
                    return {
                        "id": job_id,
                        "status": result.get("status", "completed"),
                        "workflow_id": body.get("workflow_id"),
                        "progress": 100,
                        "output": result.get("result", result),
                    }
                else:
                    return {"status": "ok", "jobs": [], "total": 0}

            elif path.startswith("/v1/jobs/"):
                job_id = path.removeprefix("/v1/jobs/")
                return {
                    "id": job_id,
                    "status": "not_found",
                    "error": "Rastreamento de jobs não disponível no modo serverless.",
                }

            else:
                return {
                    "success": False,
                    "error": {"code": "NOT_FOUND", "message": f"Route {path} not mapped in Serverless."},
                }

        except Exception as e:
            return {"success": False, "error": {"code": "HANDLER_ERROR", "message": str(e)}}

    return await _runtime.handle(job)


runpod.serverless.start({"handler": handler})
