from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.v1.schemas import ModelListResponse, ModelResponse
from src.application.models.get_model import GetModelUseCase
from src.application.models.list_models import ListModelsUseCase
from src.config.dependencies import get_get_model_uc, get_list_models_uc
from src.domain.entities.model import AIModel

router = APIRouter(prefix="/models", tags=["Models"])


def _to_response(model: AIModel) -> ModelResponse:
    return ModelResponse(
        id=model.id,
        name=model.name,
        provider_type=model.provider_type,
        capabilities=model.capabilities,
        status=model.status,
        version=model.version,
        requirements=model.requirements,
    )


@router.get("", response_model=ModelListResponse)
async def list_models(
    capability: str | None = Query(None),
    uc: ListModelsUseCase = Depends(get_list_models_uc),
) -> ModelListResponse:
    result = await uc.execute(capability=capability)
    return ModelListResponse(models=[_to_response(m) for m in result.models])


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: str,
    uc: GetModelUseCase = Depends(get_get_model_uc),
) -> ModelResponse:
    try:
        model = await uc.execute(model_id)
        return _to_response(model)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
