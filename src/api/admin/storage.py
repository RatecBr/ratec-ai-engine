from fastapi import APIRouter, Depends
from src.api.admin.dependencies import verify_admin_token
from src.api.admin.responses import admin_success, AdminResponse
from src.application.admin import storage_service

router = APIRouter(
    prefix="/storage",
    tags=["Admin Storage"],
    dependencies=[Depends(verify_admin_token)]
)

@router.get("")
def get_storage() -> AdminResponse:
    data = storage_service.get_storage_info()
    return admin_success(data)
