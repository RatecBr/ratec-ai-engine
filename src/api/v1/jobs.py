from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.v1.schemas import JobListResponse, JobResponse, SubmitJobRequest
from src.application.jobs.cancel_job import CancelJobUseCase
from src.application.jobs.get_job_status import GetJobStatusUseCase
from src.application.jobs.list_jobs import ListJobsInput, ListJobsUseCase
from src.application.jobs.submit_job import SubmitJobInput, SubmitJobUseCase
from src.config.dependencies import get_cancel_job_uc, get_get_job_status_uc, get_list_jobs_uc, get_submit_job_uc
from src.domain.entities.job import Job, JobStatus

router = APIRouter(prefix="/jobs", tags=["Jobs"])


def _to_response(job: Job) -> JobResponse:
    return JobResponse(
        id=job.id,
        workflow_id=job.workflow_id,
        status=job.status,
        input=job.input,
        output=job.output,
        error=job.error,
        provider_job_id=job.provider_job_id,
        created_at=job.created_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at,
    )


@router.post("", response_model=JobResponse, status_code=202)
async def submit_job(
    body: SubmitJobRequest,
    uc: SubmitJobUseCase = Depends(get_submit_job_uc),
) -> JobResponse:
    try:
        result = await uc.execute(SubmitJobInput(workflow_id=body.workflow_id, input=body.input))
        return _to_response(result.job)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("", response_model=JobListResponse)
async def list_jobs(
    status: JobStatus | None = Query(None),
    workflow_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    uc: ListJobsUseCase = Depends(get_list_jobs_uc),
) -> JobListResponse:
    result = await uc.execute(ListJobsInput(status=status, workflow_id=workflow_id, limit=limit, offset=offset))
    return JobListResponse(jobs=[_to_response(j) for j in result.jobs], total=result.total)


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    uc: GetJobStatusUseCase = Depends(get_get_job_status_uc),
) -> JobResponse:
    try:
        result = await uc.execute(job_id)
        return _to_response(result.job)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/{job_id}/cancel", response_model=JobResponse)
async def cancel_job(
    job_id: str,
    uc: CancelJobUseCase = Depends(get_cancel_job_uc),
) -> JobResponse:
    try:
        job = await uc.execute(job_id)
        return _to_response(job)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
