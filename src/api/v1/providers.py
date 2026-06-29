from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from src.api.v1.schemas import ProviderListResponse, ProviderResponse
from src.application.providers.get_provider import GetProviderUseCase
from src.application.providers.list_providers import ListProvidersUseCase
from src.config.dependencies import get_get_provider_uc, get_list_providers_uc
from src.domain.entities.provider import Provider

router = APIRouter(prefix="/providers", tags=["Providers"])


def _to_response(provider: Provider) -> ProviderResponse:
    return ProviderResponse(
        id=provider.id,
        name=provider.name,
        type=provider.type,
        status=provider.status,
        capabilities=provider.capabilities,
    )


@router.get("", response_model=ProviderListResponse)
async def list_providers(uc: ListProvidersUseCase = Depends(get_list_providers_uc)) -> ProviderListResponse:
    result = await uc.execute()
    return ProviderListResponse(providers=[_to_response(p) for p in result.providers])


@router.get("/{provider_id}", response_model=ProviderResponse)
async def get_provider(
    provider_id: str,
    uc: GetProviderUseCase = Depends(get_get_provider_uc),
) -> ProviderResponse:
    try:
        provider = await uc.execute(provider_id)
        return _to_response(provider)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
