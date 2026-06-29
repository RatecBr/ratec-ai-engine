from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from src.api.v1.schemas import WorkflowListResponse, WorkflowResponse, WorkflowStepResponse
from src.application.workflows.get_workflow import GetWorkflowUseCase
from src.application.workflows.list_workflows import ListWorkflowsUseCase
from src.config.dependencies import get_get_workflow_uc, get_list_workflows_uc
from src.domain.entities.workflow import Workflow

router = APIRouter(prefix="/workflows", tags=["Workflows"])


def _to_response(workflow: Workflow) -> WorkflowResponse:
    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        description=workflow.description,
        version=workflow.version,
        steps=[
            WorkflowStepResponse(
                id=s.id,
                provider_type=s.provider_type,
                action=s.action,
                parameters=s.parameters,
                depends_on=s.depends_on,
            )
            for s in workflow.steps
        ],
        input_schema=workflow.input_schema,
        output_schema=workflow.output_schema,
    )


@router.get("", response_model=WorkflowListResponse)
async def list_workflows(uc: ListWorkflowsUseCase = Depends(get_list_workflows_uc)) -> WorkflowListResponse:
    result = await uc.execute()
    return WorkflowListResponse(workflows=[_to_response(w) for w in result.workflows])


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    uc: GetWorkflowUseCase = Depends(get_get_workflow_uc),
) -> WorkflowResponse:
    try:
        workflow = await uc.execute(workflow_id)
        return _to_response(workflow)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
