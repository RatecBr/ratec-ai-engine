"""
RATEC AI ENGINE — RunPod Serverless Handler
Ponto de entrada do ambiente Serverless.
import os
import json
import runpod
from runtime import Runtime
from src.application.admin.version_provider import version_provider

_runtime = Runtime.initialize()

# Print build info from provider
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
    Ele processa execuções legadas de Inteligência Artificial (workflow_id)
    e atende as requisições de controle do Console Web (http_path),
    tudo sem carregar o framework FastAPI para manter o container super leve.
    """
    job_input = job.get("input", {})
    
    # 1. Se for uma requisição do Gateway da Vercel (API Route /api/[...path])
    if "http_path" in job_input:
        path = job_input.get("http_path", "/")
        
        try:
            # Em vez de carregar FastAPI, batemos direto nos serviços limpos!
            # Isso respeita a regra do Dockerfile.serverless (sem FastAPI/Pydantic)
            if path == "/admin/version":
                # Inject GPU metadata safely
                gpu_model = "unknown"
                try:
                    from runtime.observability import get_gpu
                    gpu_model = get_gpu().model
                except:
                    pass
                return {
                    "success": True, 
                    "data": version_provider.get_version_info(
                        boot_time=_runtime.boot_time,
                        gpu_model=gpu_model
                    )
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
                # Assumindo "all" como padrão por simplicidade no handler serverless
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
                from src.application.admin import system_service, gpu_service, runtime_service, storage_service
                data = system_service.get_system_info()
                data["gpu"] = gpu_service.get_gpu_telemetry()
                data["runtime"] = runtime_service.get_runtime_info()
                data["storage"] = storage_service.get_storage_info()
                data["comfyui_manager"] = data["runtime"]["comfyui_manager"]
                return {"success": True, "data": data}
            
            else:
                return {"success": False, "error": {"code": "NOT_FOUND", "message": f"Route {path} not mapped in Serverless."}}
                
        except Exception as e:
            return {"success": False, "error": {"code": "HANDLER_ERROR", "message": str(e)}}
            
    # 2. Execução legada / worker direto de IA
    return await _runtime.handle(job)


runpod.serverless.start({"handler": handler})
