from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import get_scheduler_service
from app.schemas.scheduler import SchedulerJobCreateRequest
from app.services.scheduler_service import SchedulerService

router = APIRouter()


@router.get("/jobs")
def list_jobs(service: SchedulerService = Depends(get_scheduler_service)) -> list[dict]:
    return service.list_jobs()


@router.post("/jobs")
def create_job(payload: SchedulerJobCreateRequest, service: SchedulerService = Depends(get_scheduler_service)) -> dict:
    return service.create_job(payload.model_dump())


@router.delete("/jobs/{job_id}")
def delete_job(job_id: str, service: SchedulerService = Depends(get_scheduler_service)) -> dict:
    return service.delete_job(job_id)


@router.post("/run/{job_id}")
def run_job(job_id: str, service: SchedulerService = Depends(get_scheduler_service)) -> dict:
    return service.run_job(job_id)
