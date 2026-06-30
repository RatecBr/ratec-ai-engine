from fastapi import APIRouter, Depends
from src.api.admin.dependencies import verify_admin_token
from src.api.admin.responses import admin_success, AdminResponse
from src.application.admin import models_service

router = APIRouter(
    prefix="/models",
    tags=["Admin Models"],
    dependencies=[Depends(verify_admin_token)]
)

@router.get("")
def get_models() -> AdminResponse:
    data = models_service.get_installed_models()
    return admin_success(data)
