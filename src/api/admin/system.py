from fastapi import APIRouter, Depends
from src.api.admin.dependencies import verify_admin_token
from src.api.admin.responses import admin_success, AdminResponse
from src.application.admin import system_service
from src.application.admin import gpu_service
from src.application.admin import runtime_service
from src.application.admin import storage_service

router = APIRouter(
    prefix="/system",
    tags=["Admin System"],
    dependencies=[Depends(verify_admin_token)]
)

@router.get("")
def get_system() -> AdminResponse:
    """
    Retorna métricas do SO (CPU, RAM).
    Para retrocompatibilidade com SystemPage do Console, também agrega runtime e gpu.
    Idealmente no front-end cada card bateria em seu endpoint dedicado.
    """
    data = system_service.get_system_info()
    data["gpu"] = gpu_service.get_gpu_telemetry()
    data["runtime"] = runtime_service.get_runtime_info()
    data["storage"] = storage_service.get_storage_info()
    data["comfyui_manager"] = data["runtime"]["comfyui_manager"]
    return admin_success(data)
