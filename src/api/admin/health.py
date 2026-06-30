from fastapi import APIRouter, Depends
from src.api.admin.dependencies import verify_admin_token
from src.api.admin.responses import admin_success, AdminResponse
from src.application.admin import health_service

router = APIRouter(
    prefix="/health",
    tags=["Admin Health"],
    dependencies=[Depends(verify_admin_token)]
)

@router.get("")
def get_health() -> AdminResponse:
    """
    Retorna estado geral da plataforma, uptime e versão.
    """
    data = health_service.get_platform_health()
    return admin_success(data)
