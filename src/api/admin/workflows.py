from fastapi import APIRouter, Depends
from src.api.admin.dependencies import verify_admin_token
from src.api.admin.responses import admin_success, AdminResponse
from src.application.admin import workflows_service

router = APIRouter(
    prefix="/workflows",
    tags=["Admin Workflows"],
    dependencies=[Depends(verify_admin_token)]
)

@router.get("")
def get_workflows() -> AdminResponse:
    data = workflows_service.get_registered_workflows()
    return admin_success(data)
