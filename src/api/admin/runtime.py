from fastapi import APIRouter, Depends
from src.api.admin.dependencies import verify_admin_token
from src.api.admin.responses import admin_success, AdminResponse
from src.application.admin import runtime_service

router = APIRouter(
    prefix="/runtime",
    tags=["Admin Runtime"],
    dependencies=[Depends(verify_admin_token)]
)

@router.get("")
def get_runtime() -> AdminResponse:
    """
    Retorna configurações de ambiente e estado do ComfyUI.
    """
    data = runtime_service.get_runtime_info()
    return admin_success(data)
