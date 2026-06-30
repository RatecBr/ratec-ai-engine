from fastapi import APIRouter, Depends
from src.api.admin.dependencies import verify_admin_token
from src.api.admin.responses import admin_success, AdminResponse
from src.application.admin import gpu_service

router = APIRouter(
    prefix="/gpu",
    tags=["Admin GPU"],
    dependencies=[Depends(verify_admin_token)]
)

@router.get("")
def get_gpu() -> AdminResponse:
    data = gpu_service.get_gpu_telemetry()
    return admin_success(data)
