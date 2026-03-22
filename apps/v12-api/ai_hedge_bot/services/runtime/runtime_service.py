from __future__ import annotations

from time import perf_counter

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.contracts.reason_codes import EXECUTION_DISABLED, build_reason
from ai_hedge_bot.contracts.runtime_events import CYCLE_COMPLETED, CYCLE_FAILED, CYCLE_STARTED, build_runtime_event
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id
from ai_hedge_bot.execution.state_machine import ExecutionStateInput, classify_execution_state
from ai_hedge_bot.orchestrator.orchestration_service import OrchestrationService
from ai_hedge_bot.repositories.audit_repository import AuditRepository
from ai_hedge_bot.repositories.runtime_repository import RuntimeRepository
from ai_hedge_bot.repositories.scheduler_repository import SchedulerRepository
from ai_hedge_bot.services.runtime.run_context import RunContext, StepContext


class RuntimeService:
    def __init__(self) -> None:
        self.runtime_repo = RuntimeRepository()
        self.scheduler_repo = SchedulerRepository()
        self.audit_repo = AuditRepository()
        self.orchestrator = OrchestrationService()

    def seed_defaults(self) -> None:
        self.scheduler_repo.seed_defaults(utc_now_iso())

    def _ensure_control_state_table(self) -> None:
        CONTAINER.runtime_store.execute(
            """
            CREATE TABLE IF NOT EXISTS runtime_control_state (
                state_id VARCHAR,
                trading_state VARCHAR,
                note VARCHAR,
                created_at TIMESTAMP
            )
            """
        )

    def get_trading_state(self) -> dict:
        self._ensure_control_state_table()
        row = CONTAINER.runtime_store.fetchone_dict(
            "SELECT state_id, trading_state, note, CAST(created_at AS VARCHAR) AS created_at FROM runtime_control_state ORDER BY created_at DESC LIMIT 1"
        )
        if not row:
            return {"state_id": None, "trading_state": "running", "note": "", "as_of": utc_now_iso()}
        return {
            "state_id": row.get("state_id"),
            "trading_state": row.get("trading_state") or "running",
            "note": row.get("note") or "",
            "as_of": row.get("created_at") or utc_now_iso(),
        }

    def set_trading_state(self, trading_state: str, note: str = "") -> dict:
        self._ensure_control_state_table()
        payload = {
            "state_id": new_cycle_id(),
            "trading_state": str(trading_state or "running"),
            "note": note,
            "created_at": utc_now_iso(),
        }
        CONTAINER.runtime_store.append("runtime_control_state", payload)
        return {
            "state_id": payload["state_id"],
            "trading_state": payload["trading_state"],
            "note": payload["note"],
            "as_of": payload["created_at"],
        }

    def cancel_open_execution_orders(self, reason: str) -> int:
        self.orchestrator._truth.ensure_schema()
        now = utc_now_iso()
        before = CONTAINER.runtime_store.fetchone_dict(
            """
            SELECT COUNT(*) AS cnt
            FROM execution_orders
            WHERE lower(coalesce(status, '')) IN ('submitted', 'partially_filled')
            """
        ) or {"cnt": 0}
        cancelled = int(before.get("cnt", 0) or 0)
        if cancelled <= 0:
            return 0

        CONTAINER.runtime_store.execute(
            """
            UPDATE execution_orders
            SET status = 'cancelled',
                updated_at = ?,
                metadata_json = CASE
                    WHEN metadata_json IS NULL OR metadata_json = '' THEN ?
                    ELSE metadata_json
                END
            WHERE lower(coalesce(status, '')) IN ('submitted', 'partially_filled')
            """,
            [now, CONTAINER.runtime_store.to_json({"cancel_reason": reason, "cancelled_at": now})],
        )
        return cancelled

    def _append_execution_halt_snapshot(self, trading_state: str, note: str, cancelled_orders: int) -> None:
        now = utc_now_iso()
        latest_plan = CONTAINER.runtime_store.fetchone_dict(
            "SELECT plan_id FROM execution_plans ORDER BY created_at DESC LIMIT 1"
        ) or {}
        latest_fill = CONTAINER.runtime_store.fetchone_dict(
            "SELECT fill_id FROM execution_fills ORDER BY created_at DESC LIMIT 1"
        ) or {}

        execution_state = classify_execution_state(
            ExecutionStateInput(
                trading_state=trading_state,
                active_plan_count=0,
                expired_plan_count=0,
                open_order_count=0,
                submitted_order_count=0,
                fill_count=0,
                planner_age_sec=0.0,
                execution_age_sec=0.0,
                last_fill_age_sec=0.0,
                reasons=("risk_halted" if trading_state == "halted" else "paused",),
            )
        )

        CONTAINER.runtime_store.append("execution_state_snapshots", {
            "as_of": now,
            "trading_state": trading_state,
            "execution_state": execution_state,
            "reason": "risk_halted" if trading_state == "halted" else "paused",
            "planner_age_sec": 0.0,
            "execution_age_sec": 0.0,
            "last_fill_age_sec": 0.0,
            "open_order_count": 0,
            "active_plan_count": 0,
            "expired_plan_count": 0,
            "latest_plan_id": latest_plan.get("plan_id"),
            "latest_order_id": None,
            "latest_fill_id": latest_fill.get("fill_id"),
        })
        CONTAINER.runtime_store.append("execution_block_reasons", {
            "as_of": now,
            "code": "risk_halted" if trading_state == "halted" else "paused",
            "severity": "critical" if trading_state == "halted" else "high",
            "message": f"Execution blocked by trading_state={trading_state}",
            "details_json": CONTAINER.runtime_store.to_json({
                "note": note,
                "cancelled_open_orders": cancelled_orders,
            }),
        })

    def _append_runtime_event(self, payload: dict) -> None:
        self.runtime_repo.create_event(payload)

    def halt_trading(self, note: str = "Kill switch triggered", actor: str = "system") -> dict:
        state = self.set_trading_state("halted", note)
        cancelled_orders = self.cancel_open_execution_orders("risk_halted")
        self._append_execution_halt_snapshot("halted", note, cancelled_orders)
        self.audit_repo.create_log(
            {
                "audit_id": new_cycle_id(),
                "category": "runtime",
                "event_type": "kill_switch",
                "run_id": None,
                "created_at": state["as_of"],
                "payload_json": CONTAINER.runtime_store.to_json({
                    "trading_state": "halted",
                    "note": note,
                    "cancelled_open_orders": cancelled_orders,
                }),
                "actor": actor,
            }
        )
        return {**state, "cancelled_open_orders": cancelled_orders}

    def resume_trading(self, note: str = "Runtime resumed", actor: str = "system") -> dict:
        state = self.set_trading_state("running", note)
        self.audit_repo.create_log(
            {
                "audit_id": new_cycle_id(),
                "category": "runtime",
                "event_type": "resume",
                "run_id": None,
                "created_at": state["as_of"],
                "payload_json": CONTAINER.runtime_store.to_json({
                    "trading_state": "running",
                    "note": note,
                }),
                "actor": actor,
            }
        )
        return state

    def run_once(self, mode: str | None = None, job_name: str = "runtime_run_once", triggered_by: str = "api") -> dict:
        self.seed_defaults()
        trading_state = self.get_trading_state()
        blocked_state = str(trading_state.get("trading_state", "running")).lower()
        if blocked_state in {"halted", "paused"}:
            run_id = new_cycle_id()
            cycle_id = new_cycle_id()
            as_of = utc_now_iso()
            reason = build_reason(
                EXECUTION_DISABLED,
                detail={
                    "trading_state": blocked_state,
                    "note": trading_state.get("note", ""),
                },
            )
            self._append_runtime_event(
                build_runtime_event(
                    event_type=CYCLE_FAILED,
                    run_id=run_id,
                    cycle_id=cycle_id,
                    mode=mode or CONTAINER.mode.value,
                    source="runtime_service",
                    severity=reason["severity"],
                    status="blocked",
                    summary=f"Runtime blocked by trading_state={blocked_state}",
                    reason_code=reason["code"],
                    details=reason["details"],
                    timestamp=as_of,
                )
            )
            return {
                "status": "blocked",
                "blocked": True,
                "run_id": run_id,
                "cycle_id": cycle_id,
                "trading_state": trading_state.get("trading_state"),
                "message": f"runtime blocked: trading_state={trading_state.get('trading_state')}",
                "reason_code": reason["code"],
                "as_of": as_of,
            }
        effective_mode = mode or CONTAINER.mode.value
        ctx = RunContext(job_name=job_name, mode=effective_mode, triggered_by=triggered_by)
        cycle_id = new_cycle_id()
        self.runtime_repo.create_run(
            {
                "run_id": ctx.run_id,
                "job_name": ctx.job_name,
                "mode": ctx.mode,
                "started_at": ctx.started_at,
                "finished_at": None,
                "status": "running",
                "error_message": None,
                "duration_ms": None,
                "triggered_by": ctx.triggered_by,
                "created_at": ctx.started_at,
            }
        )
        self.audit_repo.create_log(
            {
                "audit_id": new_cycle_id(),
                "category": "runtime",
                "event_type": "run_started",
                "run_id": ctx.run_id,
                "created_at": ctx.started_at,
                "payload_json": CONTAINER.runtime_store.to_json({"job_name": ctx.job_name, "mode": ctx.mode}),
                "actor": triggered_by,
            }
        )

        sched_id = new_cycle_id()
        self.scheduler_repo.create_run(
            {
                "scheduler_run_id": sched_id,
                "job_id": job_name,
                "run_id": ctx.run_id,
                "trigger_type": triggered_by,
                "status": "running",
                "started_at": ctx.started_at,
                "finished_at": None,
                "duration_ms": None,
                "error_message": None,
            }
        )
        self._append_runtime_event(
            build_runtime_event(
                event_type=CYCLE_STARTED,
                run_id=ctx.run_id,
                cycle_id=cycle_id,
                mode=ctx.mode,
                source="runtime_service",
                status="running",
                summary=f"Runtime cycle started via {ctx.triggered_by}",
                details={"job_name": ctx.job_name, "triggered_by": ctx.triggered_by},
                timestamp=ctx.started_at,
            )
        )
        try:
            step = self._start_step(ctx, "orchestrator_cycle")
            result = self.orchestrator.run(ctx.mode, run_id=ctx.run_id, cycle_id=cycle_id)
            self._finish_step(step, payload=result)

            checkpoint_payload = {
                "checkpoint_id": new_cycle_id(),
                "run_id": ctx.run_id,
                "checkpoint_name": "latest_orchestrator_run",
                "created_at": utc_now_iso(),
                "payload_json": CONTAINER.runtime_store.to_json(result),
            }
            self.runtime_repo.create_checkpoint(checkpoint_payload)
            self.audit_repo.create_log(
                {
                    "audit_id": new_cycle_id(),
                    "category": "runtime",
                    "event_type": "checkpoint_created",
                    "run_id": ctx.run_id,
                    "created_at": checkpoint_payload["created_at"],
                    "payload_json": checkpoint_payload["payload_json"],
                    "actor": triggered_by,
                }
            )

            finished_at = utc_now_iso()
            duration_ms = int((perf_counter() - ctx.started_perf) * 1000)
            self.runtime_repo.update_run(ctx.run_id, status="success", finished_at=finished_at, duration_ms=duration_ms)
            self.scheduler_repo.finalize_run(sched_id, status="success", finished_at=finished_at, duration_ms=duration_ms, run_id=ctx.run_id)
            self.audit_repo.create_log(
                {
                    "audit_id": new_cycle_id(),
                    "category": "runtime",
                    "event_type": "run_finished",
                    "run_id": ctx.run_id,
                    "created_at": finished_at,
                    "payload_json": CONTAINER.runtime_store.to_json({"status": "success"}),
                    "actor": triggered_by,
                }
            )
            self._append_runtime_event(
                build_runtime_event(
                    event_type=CYCLE_COMPLETED,
                    run_id=ctx.run_id,
                    cycle_id=cycle_id,
                    mode=ctx.mode,
                    source="runtime_service",
                    status="ok",
                    summary="Runtime cycle completed successfully.",
                    details={"result_status": result.get("status"), "details": result.get("details", {})},
                    timestamp=finished_at,
                )
            )
            return {"status": "ok", "run_id": ctx.run_id, "mode": ctx.mode, "result": result}
        except Exception as exc:
            finished_at = utc_now_iso()
            duration_ms = int((perf_counter() - ctx.started_perf) * 1000)
            self.runtime_repo.update_run(ctx.run_id, status="failed", finished_at=finished_at, duration_ms=duration_ms, error_message=str(exc))
            self.scheduler_repo.finalize_run(sched_id, status="failed", finished_at=finished_at, duration_ms=duration_ms, error_message=str(exc), run_id=ctx.run_id)
            self.audit_repo.create_log(
                {
                    "audit_id": new_cycle_id(),
                    "category": "runtime",
                    "event_type": "run_failed",
                    "run_id": ctx.run_id,
                    "created_at": finished_at,
                    "payload_json": CONTAINER.runtime_store.to_json({"error": str(exc)}),
                    "actor": triggered_by,
                }
            )
            self._append_runtime_event(
                build_runtime_event(
                    event_type=CYCLE_FAILED,
                    run_id=ctx.run_id,
                    cycle_id=cycle_id,
                    mode=ctx.mode,
                    source="runtime_service",
                    severity="critical",
                    status="failed",
                    summary="Runtime cycle failed.",
                    details={"error": str(exc)},
                    timestamp=finished_at,
                )
            )
            raise

    def list_runs(self, limit: int = 20) -> list[dict]:
        return self.runtime_repo.list_runs(limit=limit)

    def get_run(self, run_id: str) -> dict | None:
        run = self.runtime_repo.get_run(run_id)
        if not run:
            return None
        run["audit_logs"] = self.audit_repo.list_logs(run_id=run_id, limit=50)
        return run

    def list_scheduler_jobs(self) -> list[dict]:
        self.seed_defaults()
        jobs = self.scheduler_repo.list_jobs()
        trading_state = str(self.get_trading_state().get("trading_state", "running") or "running").lower()
        execution_job_tokens = ("cycle", "runtime", "orchestrator", "paper", "shadow", "rebalance")
        for job in jobs:
            identity = " ".join([
                str(job.get("job_id", "") or ""),
                str(job.get("job_name", "") or ""),
                str(job.get("mode", "") or ""),
            ]).lower()
            is_execution_job = any(token in identity for token in execution_job_tokens)
            job["execution_blocked"] = bool(is_execution_job and trading_state in {"halted", "paused"})
            job["trading_state"] = trading_state
            if job["execution_blocked"]:
                job["status"] = trading_state
            else:
                job["status"] = "running" if bool(job.get("enabled", True)) else "paused"
        return jobs

    def list_scheduler_runs(self, limit: int = 20) -> list[dict]:
        return self.scheduler_repo.list_runs(limit=limit)

    def _start_step(self, ctx: RunContext, step_name: str) -> StepContext:
        step = ctx.new_step(step_name)
        self.runtime_repo.create_step(
            {
                "step_id": step.step_id,
                "run_id": ctx.run_id,
                "step_name": step.step_name,
                "status": "running",
                "started_at": step.started_at,
                "finished_at": None,
                "duration_ms": None,
                "error_message": None,
                "payload_json": None,
            }
        )
        return step

    def _finish_step(self, step: StepContext, payload: dict | None = None, error_message: str | None = None) -> None:
        finished_at = utc_now_iso()
        duration_ms = int((perf_counter() - step.started_perf) * 1000)
        status = "failed" if error_message else "success"
        self.runtime_repo.update_step(
            step.step_id,
            status=status,
            finished_at=finished_at,
            duration_ms=duration_ms,
            error_message=error_message,
            payload_json=CONTAINER.runtime_store.to_json(payload) if payload is not None else None,
        )
