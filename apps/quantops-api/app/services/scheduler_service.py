from __future__ import annotations

from app.repositories.audit_repository import AuditRepository
from app.repositories.scheduler_repository import SchedulerRepository
from app.repositories.risk_repository import RiskRepository
from app.core.trading_state import is_execution_job, should_block_execution


class SchedulerService:
    def __init__(self, scheduler_repository: SchedulerRepository, audit_repository: AuditRepository, risk_repository: RiskRepository) -> None:
        self.scheduler_repository = scheduler_repository
        self.audit_repository = audit_repository
        self.risk_repository = risk_repository

    def list_jobs(self) -> list[dict]:
        trading_state = self.risk_repository.get_trading_state().get("trading_state", "running")
        return self.scheduler_repository.list_jobs(trading_state=trading_state)

    def create_job(self, payload: dict) -> dict:
        payload.setdefault('target_endpoint', '/orchestrator/paper/run-cycle')
        saved = self.scheduler_repository.upsert_job(payload)
        self.audit_repository.log_action(category='scheduler', event_type='job_upsert', payload_json=str(saved))
        return saved

    def delete_job(self, job_id: str) -> dict:
        self.scheduler_repository.delete_job(job_id)
        self.audit_repository.log_action(category='scheduler', event_type='job_delete', payload_json=job_id)
        return {'ok': True, 'message': f'deleted {job_id}'}

    def run_job(self, job_id: str) -> dict:
        trading_state = self.risk_repository.get_trading_state().get("trading_state", "running")
        if should_block_execution(trading_state, execution_job=is_execution_job(job_id=job_id)):
            result = {"ok": False, "blocked": True, "job_id": job_id, "run_status": trading_state, "message": f"blocked {job_id}: trading_state={trading_state}"}
            self.audit_repository.log_action(category="scheduler", event_type="job_run_blocked", payload_json=str(result))
            return result
        result = self.scheduler_repository.record_run(job_id, trigger_type='manual')
        self.audit_repository.log_action(category='scheduler', event_type='job_run', payload_json=str(result))
        return {'ok': True, 'message': f'ran {job_id}', **result}

    def pause_job(self, job_id: str) -> dict:
        result = self.scheduler_repository.set_enabled(job_id, False)
        self.audit_repository.log_action(category='scheduler', event_type='job_pause', payload_json=str(result))
        return {'ok': True, 'message': f'paused {job_id}', **result}

    def resume_job(self, job_id: str) -> dict:
        result = self.scheduler_repository.set_enabled(job_id, True)
        self.audit_repository.log_action(category='scheduler', event_type='job_resume', payload_json=str(result))
        return {'ok': True, 'message': f'resumed {job_id}', **result}
