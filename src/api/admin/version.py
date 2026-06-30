from fastapi import APIRouter, Depends
from src.api.admin.dependencies import verify_admin_token
from src.api.admin.responses import admin_success, AdminResponse
from src.application.admin.version_provider import version_provider
from runtime import Runtime

router = APIRouter(
    prefix="/version",
    tags=["Admin System"],
    dependencies=[Depends(verify_admin_token)]
)

@router.get("")
def get_version() -> AdminResponse:
    """
    Retorna metadados de build e informações do ambiente em execução.
    """
    # Em ambiente FastAPI local (desenvolvimento), o Runtime pode não estar iniciado.
    # Tentamos obter os dados via módulos ou fallbacks seguros.
    gpu_model = "unknown"
    boot_time = None
    try:
        from runtime.observability import get_gpu
        gpu_model = get_gpu().model
    except Exception:
        pass

    try:
        from runtime import _BOOT_TIME
        boot_time = _BOOT_TIME
    except Exception:
        pass

    data = version_provider.get_version_info(
        boot_time=boot_time,
        gpu_model=gpu_model
    )
    return admin_success(data)
