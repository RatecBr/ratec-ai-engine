from fastapi import APIRouter, Depends, Query
from src.api.admin.dependencies import verify_admin_token
from src.api.admin.responses import admin_success, AdminResponse
from src.application.admin import logs_service

router = APIRouter(
    prefix="/logs",
    tags=["Admin Logs"],
    dependencies=[Depends(verify_admin_token)]
)

@router.get("")
def get_logs(type: str = Query("all")) -> AdminResponse:
    data = logs_service.get_platform_logs(type)
    return admin_success(data)
