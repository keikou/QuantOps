from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_scheduler_service, get_v12_client, get_risk_repository
from app.core.trading_state import is_execution_job, should_block_execution
from app.services.scheduler_service import SchedulerService
from app.clients.v12_client import V12Client
from app.repositories.risk_repository import RiskRepository

router = APIRouter()

@router.get('/jobs')
async def scheduler_jobs(service: SchedulerService = Depends(get_scheduler_service), client: V12Client = Depends(get_v12_client)) -> dict:
    local_jobs = service.list_jobs()
    if local_jobs:
        return {'items': local_jobs}
    return await client.get_sprint5c_scheduler_jobs()

@router.get('/runs')
async def scheduler_runs(client: V12Client = Depends(get_v12_client)) -> dict:
    return await client.get_sprint5c_scheduler_runs()

@router.post('/run-now')
async def run_now(mode: str | None = Query(default=None), client: V12Client = Depends(get_v12_client), risk_repository: RiskRepository = Depends(get_risk_repository)) -> dict:
    trading_state = risk_repository.get_trading_state().get("trading_state", "running")
    if str(trading_state).lower() in {"halted", "paused"}:
        return {"ok": False, "blocked": True, "run_status": trading_state, "message": f"run-now blocked: trading_state={trading_state}"}
    if mode:
        return await client.run_with_mode(mode=mode)
    return await client.run_sprint5c_cycle()

@router.post('/jobs/create')
def create_job(payload: dict, service: SchedulerService = Depends(get_scheduler_service)) -> dict:
    return service.create_job(payload)

@router.delete('/jobs/{job_id}')
def delete_job(job_id: str, service: SchedulerService = Depends(get_scheduler_service)) -> dict:
    return service.delete_job(job_id)

@router.post('/jobs/{job_id}/run')
def run_job(job_id: str, service: SchedulerService = Depends(get_scheduler_service), risk_repository: RiskRepository = Depends(get_risk_repository)) -> dict:
    trading_state = risk_repository.get_trading_state().get("trading_state", "running")
    if should_block_execution(trading_state, execution_job=is_execution_job(job_id=job_id)):
        return {"ok": False, "blocked": True, "job_id": job_id, "run_status": trading_state, "message": f"run blocked: trading_state={trading_state}"}
    return service.run_job(job_id)

@router.post('/jobs/{job_id}/pause')
def pause_job(job_id: str, service: SchedulerService = Depends(get_scheduler_service)) -> dict:
    return service.pause_job(job_id)

@router.post('/jobs/{job_id}/resume')
def resume_job(job_id: str, service: SchedulerService = Depends(get_scheduler_service), risk_repository: RiskRepository = Depends(get_risk_repository)) -> dict:
    trading_state = risk_repository.get_trading_state().get("trading_state", "running")
    if should_block_execution(trading_state, execution_job=is_execution_job(job_id=job_id)):
        return {"ok": False, "blocked": True, "job_id": job_id, "run_status": trading_state, "message": f"resume blocked: trading_state={trading_state}"}
    return service.resume_job(job_id)
