from fastapi import APIRouter, Depends
from src.api.admin.dependencies import verify_admin_token
from src.api.admin.responses import admin_success, AdminResponse
from src.application.admin import metrics_service

router = APIRouter(
    prefix="/metrics",
    tags=["Admin Metrics"],
    dependencies=[Depends(verify_admin_token)]
)

@router.get("")
def get_metrics() -> AdminResponse:
    data = metrics_service.get_system_metrics()
    return admin_success(data)
