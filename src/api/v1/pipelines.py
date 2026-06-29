from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from src.api.v1.schemas import PipelineListResponse, PipelineResponse, PipelineStepResponse
from src.application.pipelines.get_pipeline import GetPipelineUseCase
from src.application.pipelines.list_pipelines import ListPipelinesUseCase
from src.config.dependencies import get_get_pipeline_uc, get_list_pipelines_uc
from src.domain.entities.pipeline import Pipeline

router = APIRouter(prefix="/pipelines", tags=["Pipelines"])


def _to_response(pipeline: Pipeline) -> PipelineResponse:
    return PipelineResponse(
        id=pipeline.id,
        name=pipeline.name,
        description=pipeline.description,
        version=pipeline.version,
        steps=[
            PipelineStepResponse(
                id=s.id,
                capability=s.capability,
                action=s.action,
                parameters=s.parameters,
                model_id=s.model_id,
                execution_strategy=s.execution_strategy,
                depends_on=s.depends_on,
            )
            for s in pipeline.steps
        ],
        input_schema=pipeline.input_schema,
        output_schema=pipeline.output_schema,
    )


@router.get("", response_model=PipelineListResponse)
async def list_pipelines(uc: ListPipelinesUseCase = Depends(get_list_pipelines_uc)) -> PipelineListResponse:
    result = await uc.execute()
    return PipelineListResponse(pipelines=[_to_response(p) for p in result.pipelines])


@router.get("/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(
    pipeline_id: str,
    uc: GetPipelineUseCase = Depends(get_get_pipeline_uc),
) -> PipelineResponse:
    try:
        pipeline = await uc.execute(pipeline_id)
        return _to_response(pipeline)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
