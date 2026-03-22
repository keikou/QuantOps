from __future__ import annotations

from pydantic import BaseModel


class SchedulerJobCreateRequest(BaseModel):
    job_id: str
    job_name: str
    job_group: str
    cadence_type: str
    cadence_value: str
    owner_service: str = "quantops-scheduler"
    enabled: bool = True
    allow_manual_run: bool = True


class SchedulerJobResponse(BaseModel):
    job_id: str
    job_name: str
    job_group: str
    cadence_type: str
    cadence_value: str
    enabled: bool
    allow_manual_run: bool
    owner_service: str
    updated_at: str | None = None


class SchedulerRunResponse(BaseModel):
    ok: bool = True
    job_id: str
    run_id: str
    trigger_type: str
    run_status: str
