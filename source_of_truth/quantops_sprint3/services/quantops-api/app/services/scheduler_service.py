from __future__ import annotations

from app.repositories.audit_repository import AuditRepository
from app.repositories.scheduler_repository import SchedulerRepository


class SchedulerService:
    def __init__(self, scheduler_repository: SchedulerRepository, audit_repository: AuditRepository) -> None:
        self.scheduler_repository = scheduler_repository
        self.audit_repository = audit_repository

    def list_jobs(self) -> list[dict]:
        return self.scheduler_repository.list_jobs()

    def create_job(self, payload: dict) -> dict:
        payload.setdefault("target_endpoint", "/orchestrator/paper/run-cycle")
        saved = self.scheduler_repository.upsert_job(payload)
        self.audit_repository.log_action(category="scheduler", event_type="job_upsert", payload_json=str(saved))
        return saved

    def delete_job(self, job_id: str) -> dict:
        self.scheduler_repository.delete_job(job_id)
        self.audit_repository.log_action(category="scheduler", event_type="job_delete", payload_json=job_id)
        return {"ok": True, "message": f"deleted {job_id}"}

    def run_job(self, job_id: str) -> dict:
        result = self.scheduler_repository.record_run(job_id, trigger_type="manual")
        self.audit_repository.log_action(category="scheduler", event_type="job_run", payload_json=str(result))
        return result
