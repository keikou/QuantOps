from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from app.clients.v12_client import V12Client, utc_now_iso
from app.services.dashboard_service import DashboardService
from app.services.portfolio_service import PortfolioService
from app.services.risk_service import RiskService
from app.services.analytics_service import AnalyticsService
from app.services.monitoring_service import MonitoringService
from app.services.alert_service import AlertService
from app.services.scheduler_service import SchedulerService
from app.services.control_service import ControlService
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.risk_repository import RiskRepository
from app.services.notification_service import NotificationService


class CommandCenterService:
    ARTIFACT_ROOT = Path(__file__).resolve().parents[4] / "test_bundle" / "artifacts" / "runtime_diagnostics"

    def __init__(
        self,
        v12_client: V12Client,
        dashboard_service: DashboardService,
        portfolio_service: PortfolioService,
        risk_service: RiskService,
        analytics_service: AnalyticsService,
        monitoring_service: MonitoringService,
        alert_service: AlertService,
        scheduler_service: SchedulerService,
        control_service: ControlService,
        analytics_repository: AnalyticsRepository,
        audit_repository: AuditRepository,
        risk_repository: RiskRepository,
        notification_service: NotificationService,
    ) -> None:
        self.v12_client = v12_client
        self.dashboard_service = dashboard_service
        self.portfolio_service = portfolio_service
        self.risk_service = risk_service
        self.analytics_service = analytics_service
        self.monitoring_service = monitoring_service
        self.alert_service = alert_service
        self.scheduler_service = scheduler_service
        self.control_service = control_service
        self.analytics_repository = analytics_repository
        self.audit_repository = audit_repository
        self.risk_repository = risk_repository
        self.notification_service = notification_service

    @staticmethod
    def _snapshot_age_sec(value: object) -> float | None:
        if not value:
            return None
        try:
            ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            else:
                ts = ts.astimezone(timezone.utc)
            return round(max(0.0, (datetime.now(timezone.utc) - ts).total_seconds()), 3)
        except Exception:
            return None

    @staticmethod
    def _parse_timestamp(value: object) -> datetime | None:
        if not value:
            return None
        try:
            ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            return ts.astimezone(timezone.utc)
        except Exception:
            return None

    def _latest_event_timestamp(
        self,
        events: list[dict],
        *,
        event_type: str,
        status: str | None = None,
    ) -> str | None:
        latest: tuple[datetime, str] | None = None
        for item in events:
            if str(item.get("event_type") or "") != event_type:
                continue
            if status is not None and str(item.get("status") or "") != status:
                continue
            raw_timestamp = item.get("timestamp") or item.get("created_at")
            parsed = self._parse_timestamp(raw_timestamp)
            if parsed is None:
                continue
            if latest is None or parsed > latest[0]:
                latest = (parsed, str(raw_timestamp))
        return latest[1] if latest else None

    @staticmethod
    def _runtime_operator_state(bridge_state: str, *, filled_count: int, degraded_flags: list[str]) -> str:
        normalized = str(bridge_state or "no_decision")
        if filled_count > 0:
            return "filled"
        if normalized == "submitted_no_fill":
            return "submitted_no_fill"
        if normalized in {"planned_blocked", "planned_not_submitted", "no_decision"}:
            return "blocked"
        if normalized in {"failed", "cycle_failed"}:
            return "failed"
        if degraded_flags:
            return "degraded"
        return normalized

    @staticmethod
    def _timeline_items(events: list[dict], *, limit: int) -> list[dict]:
        return [
            {
                "event_type": str(item.get("event_type") or ""),
                "summary": str(item.get("summary") or ""),
                "severity": str(item.get("severity") or "info"),
                "status": str(item.get("status") or "ok"),
                "reason_code": str(item.get("reason_code") or "") or None,
                "symbol": str(item.get("symbol") or "") or None,
                "timestamp": item.get("timestamp") or item.get("created_at") or utc_now_iso(),
            }
            for item in events[:limit]
        ]

    @classmethod
    def _artifact_bundle_for_run(cls, run_id: str | None) -> dict | None:
        if not run_id:
            return None
        root = cls.ARTIFACT_ROOT
        if not root.exists():
            return None
        candidates = sorted(root.glob(f"*_{run_id}.json"), reverse=True)
        if not candidates:
            return None
        latest = candidates[0]
        return {
            "run_id": run_id,
            "path": str(latest),
            "name": latest.name,
        }

    @staticmethod
    def _find_event(events: list[dict], *event_types: str, status: str | None = None) -> dict | None:
        for item in reversed(events):
            current_type = str(item.get("event_type") or "")
            if current_type not in event_types:
                continue
            if status is not None and str(item.get("status") or "") != status:
                continue
            return item
        return None

    @staticmethod
    def _find_reason(reasons: list[dict], reason_code: str | None) -> dict | None:
        if not reason_code:
            return None
        for item in reasons:
            if str(item.get("reason_code") or "") == reason_code:
                return item
        return None

    def _runtime_stage_items(
        self,
        *,
        run: dict,
        planner: dict,
        bridge: dict,
        events: list[dict],
        reasons: list[dict],
        artifact_bundle: dict | None,
    ) -> list[dict]:
        latest_reason_code = str(bridge.get("latest_reason_code") or "") or None
        latest_reason = self._find_reason(reasons, latest_reason_code)
        cycle_started = self._find_event(events, "cycle_started")
        cycle_completed = self._find_event(events, "cycle_completed", status="ok")
        cycle_failed = self._find_event(events, "cycle_failed", status="failed") or self._find_event(events, "cycle_failed", status="blocked")
        order_submitted = self._find_event(events, "order_submitted", status="ok")
        order_blocked = self._find_event(events, "order_blocked")
        fill_recorded = self._find_event(events, "fill_recorded", status="ok")
        portfolio_updated = self._find_event(events, "portfolio_updated", status="ok")

        planner_status = str(planner.get("planner_status") or "unknown")
        bridge_state = str(bridge.get("bridge_state") or "no_decision")
        planned_count = int(bridge.get("planned_count", 0) or 0)
        submitted_count = int(bridge.get("submitted_count", 0) or 0)
        filled_count = int(bridge.get("filled_count", 0) or 0)
        checkpoints = run.get("checkpoints") if isinstance(run.get("checkpoints"), list) else []
        audit_logs = run.get("audit_logs") if isinstance(run.get("audit_logs"), list) else []

        stages = [
            {
                "key": "cycle_start",
                "title": "Cycle Start",
                "state": "completed" if cycle_started or run.get("started_at") else "missing",
                "timestamp": cycle_started.get("timestamp") if cycle_started else run.get("started_at") or run.get("created_at"),
                "summary": cycle_started.get("summary") if cycle_started else "Runtime run was created.",
                "reason_code": cycle_started.get("reason_code") if cycle_started else None,
                "evidence": [f"triggered_by={run.get('triggered_by') or 'unknown'}", f"mode={run.get('mode') or 'unknown'}"],
            },
            {
                "key": "planner_truth",
                "title": "Planner Truth",
                "state": "completed" if planner_status not in {"unknown", "blocked", "failed"} else ("blocked" if planner_status == "blocked" else "degraded" if planner_status == "failed" else "missing"),
                "timestamp": planner.get("generated_at") or run.get("started_at"),
                "summary": (
                    f"Planner status {planner_status} with {len(planner.get('items') or [])} row(s)."
                    if planner_status != "unknown"
                    else "Planner truth was not available for this run."
                ),
                "reason_code": latest_reason_code if planner_status in {"blocked", "failed"} else None,
                "evidence": [
                    f"planner_status={planner_status}",
                    f"planner_rows={len(planner.get('items') or [])}",
                    f"planned_count={planned_count}",
                ],
            },
            {
                "key": "execution_bridge",
                "title": "Execution Bridge",
                "state": (
                    "completed" if bridge_state in {"filled", "submitted_no_fill"} else
                    "blocked" if bridge_state in {"planned_blocked", "planned_not_submitted", "no_decision"} else
                    "degraded" if bridge_state in {"failed", "cycle_failed"} else
                    "missing"
                ),
                "timestamp": bridge.get("last_transition_at") or planner.get("generated_at"),
                "summary": str(bridge.get("operator_message") or bridge.get("latest_reason_summary") or f"Bridge state {bridge_state}."),
                "reason_code": latest_reason_code,
                "evidence": [
                    f"bridge_state={bridge_state}",
                    f"planned={planned_count}",
                    f"submitted={submitted_count}",
                    f"filled={filled_count}",
                ],
            },
            {
                "key": "order_submission",
                "title": "Order Submission",
                "state": (
                    "completed" if submitted_count > 0 else
                    "blocked" if planned_count > 0 or order_blocked else
                    "not_applicable"
                ),
                "timestamp": order_submitted.get("timestamp") if order_submitted else order_blocked.get("timestamp") if order_blocked else bridge.get("last_transition_at"),
                "summary": (
                    order_submitted.get("summary")
                    if order_submitted
                    else order_blocked.get("summary")
                    if order_blocked
                    else "No order submission was required for this run."
                ),
                "reason_code": order_blocked.get("reason_code") if order_blocked else latest_reason_code if submitted_count == 0 and planned_count > 0 else None,
                "evidence": [
                    f"submitted_count={submitted_count}",
                    f"blocked_count={int(bridge.get('blocked_count', 0) or 0)}",
                ],
            },
            {
                "key": "fill_capture",
                "title": "Fill Capture",
                "state": (
                    "completed" if filled_count > 0 else
                    "blocked" if submitted_count > 0 else
                    "not_applicable"
                ),
                "timestamp": fill_recorded.get("timestamp") if fill_recorded else bridge.get("last_transition_at"),
                "summary": (
                    fill_recorded.get("summary")
                    if fill_recorded
                    else "Orders were submitted but no fills were captured."
                    if submitted_count > 0
                    else "No fill stage was expected for this run."
                ),
                "reason_code": fill_recorded.get("reason_code") if fill_recorded else latest_reason_code if submitted_count > 0 and filled_count == 0 else None,
                "evidence": [
                    f"filled_count={filled_count}",
                    f"submitted_count={submitted_count}",
                ],
            },
            {
                "key": "portfolio_update",
                "title": "Portfolio Update",
                "state": (
                    "completed" if portfolio_updated else
                    "missing" if filled_count > 0 else
                    "not_applicable"
                ),
                "timestamp": portfolio_updated.get("timestamp") if portfolio_updated else None,
                "summary": (
                    portfolio_updated.get("summary")
                    if portfolio_updated
                    else "Portfolio update event is missing after fills were recorded."
                    if filled_count > 0
                    else "Portfolio update was not expected because there were no fills."
                ),
                "reason_code": portfolio_updated.get("reason_code") if portfolio_updated else None,
                "evidence": [f"last_successful_portfolio_update_at={self._latest_event_timestamp(events, event_type='portfolio_updated', status='ok') or '-'}"],
            },
            {
                "key": "artifacts",
                "title": "Artifacts & Evidence",
                "state": "completed" if artifact_bundle or checkpoints or audit_logs else "missing",
                "timestamp": run.get("finished_at") or run.get("started_at"),
                "summary": (
                    f"Artifact bundle={'yes' if artifact_bundle else 'no'}, checkpoints={len(checkpoints)}, audit_logs={len(audit_logs)}."
                ),
                "reason_code": None,
                "evidence": [
                    f"artifact_bundle={artifact_bundle.get('name') if artifact_bundle else 'missing'}",
                    f"checkpoints={len(checkpoints)}",
                    f"audit_logs={len(audit_logs)}",
                ],
            },
            {
                "key": "cycle_completion",
                "title": "Cycle Completion",
                "state": (
                    "failed" if str(run.get("status") or "") == "failed" or cycle_failed else
                    "completed" if cycle_completed or str(run.get("status") or "") in {"success", "ok"} else
                    "running"
                ),
                "timestamp": cycle_completed.get("timestamp") if cycle_completed else cycle_failed.get("timestamp") if cycle_failed else run.get("finished_at"),
                "summary": (
                    cycle_completed.get("summary")
                    if cycle_completed
                    else cycle_failed.get("summary")
                    if cycle_failed
                    else f"Run status {run.get('status') or 'unknown'}."
                ),
                "reason_code": cycle_failed.get("reason_code") if cycle_failed else latest_reason_code if str(run.get("status") or "") == "failed" else None,
                "evidence": [
                    f"run_status={run.get('status') or 'unknown'}",
                    f"duration_ms={run.get('duration_ms') or 0}",
                ],
            },
        ]
        if latest_reason is not None:
            for stage in stages:
                if stage["reason_code"] == latest_reason_code and latest_reason.get("summary"):
                    stage["evidence"].append(f"reason_summary={latest_reason.get('summary')}")
        return stages

    @staticmethod
    def _diagnosis_catalog(code: str) -> dict:
        catalog = {
            "missing_price": {
                "severity": "medium",
                "retryability": "retryable",
                "operator_action": "Check pricing source freshness, symbol mapping, and market data ingestion.",
                "likely_component": "pricing_service",
            },
            "risk_guard_block": {
                "severity": "high",
                "retryability": "watch",
                "operator_action": "Inspect guard reason, exposure, margin, and kill-switch thresholds before retrying.",
                "likely_component": "risk_guard",
            },
            "execution_bridge_missing": {
                "severity": "high",
                "retryability": "retryable",
                "operator_action": "Verify planner-to-execution handoff and execution adapter health.",
                "likely_component": "execution_bridge",
            },
            "order_not_submitted": {
                "severity": "medium",
                "retryability": "retryable",
                "operator_action": "Check whether order submission was intentionally suppressed or blocked downstream.",
                "likely_component": "execution_bridge",
            },
            "fill_not_captured": {
                "severity": "medium",
                "retryability": "watch",
                "operator_action": "Inspect broker acknowledgements and fill capture latency before retrying.",
                "likely_component": "execution_bridge",
            },
            "portfolio_not_updated": {
                "severity": "high",
                "retryability": "watch",
                "operator_action": "Confirm portfolio writer and snapshot persistence after fills.",
                "likely_component": "portfolio_writer",
            },
            "artifact_chain_incomplete": {
                "severity": "medium",
                "retryability": "investigate",
                "operator_action": "Inspect the first missing artifact and compare checkpoints against the stage timeline.",
                "likely_component": "analytics_writer",
            },
            "cycle_stalled": {
                "severity": "high",
                "retryability": "investigate",
                "operator_action": "Review runtime scheduler state and any incomplete steps before retrying.",
                "likely_component": "runtime_service",
            },
            "successful_chain": {
                "severity": "low",
                "retryability": "none",
                "operator_action": "No remediation needed. Continue monitoring for regressions.",
                "likely_component": "none",
            },
            "unknown_runtime_gap": {
                "severity": "medium",
                "retryability": "investigate",
                "operator_action": "Review the run detail evidence and raw event chain to locate the first missing truth point.",
                "likely_component": "unknown",
            },
        }
        return catalog.get(code, catalog["unknown_runtime_gap"])

    def _classify_runtime_diagnosis(
        self,
        *,
        summary: dict,
        stages: list[dict],
        artifacts: dict,
    ) -> dict:
        latest_reason_code = str(summary.get("latest_reason_code") or "").upper()
        latest_reason_summary = str(summary.get("latest_reason_summary") or "")
        blocking_component = str(summary.get("blocking_component") or "") or None
        missing_artifacts = list(artifacts.get("missing") or [])
        stage_by_key = {str(stage.get("key") or ""): stage for stage in stages}

        primary_code = "unknown_runtime_gap"
        secondary_codes: list[str] = []

        if latest_reason_code == "MISSING_PRICE":
            primary_code = "missing_price"
        elif latest_reason_code == "RISK_GUARD_BLOCK":
            primary_code = "risk_guard_block"
        elif stage_by_key.get("execution_bridge", {}).get("state") in {"blocked", "missing"} and int(summary.get("planned_count", 0) or 0) > 0:
            primary_code = "execution_bridge_missing"
        elif stage_by_key.get("order_submission", {}).get("state") == "blocked":
            primary_code = "order_not_submitted"
        elif stage_by_key.get("fill_capture", {}).get("state") == "blocked":
            primary_code = "fill_not_captured"
        elif stage_by_key.get("portfolio_update", {}).get("state") == "missing":
            primary_code = "portfolio_not_updated"
        elif stage_by_key.get("cycle_completion", {}).get("state") == "running":
            primary_code = "cycle_stalled"
        elif (
            summary.get("operator_state") == "filled"
            and stage_by_key.get("portfolio_update", {}).get("state") == "completed"
            and stage_by_key.get("cycle_completion", {}).get("state") == "completed"
        ):
            primary_code = "successful_chain"

        if missing_artifacts and str(summary.get("operator_state") or "") != "filled" and primary_code != "artifact_chain_incomplete":
            secondary_codes.append("artifact_chain_incomplete")

        catalog = self._diagnosis_catalog(primary_code)
        confidence = 0.95 if primary_code in {"missing_price", "risk_guard_block"} else 0.88 if primary_code != "unknown_runtime_gap" else 0.65
        return {
            "primary_code": primary_code,
            "secondary_codes": secondary_codes,
            "severity": catalog["severity"],
            "retryability": catalog["retryability"],
            "operator_action": catalog["operator_action"],
            "likely_component": blocking_component or catalog["likely_component"],
            "confidence": confidence,
            "summary": latest_reason_summary or str(stage_by_key.get("cycle_completion", {}).get("summary") or ""),
        }

    @staticmethod
    def _issue_trend(count_recent: int, count_older: int) -> str:
        if count_recent > count_older:
            return "up"
        if count_recent < count_older:
            return "down"
        return "flat"

    @staticmethod
    def _issue_recurrence_status(total_count: int, count_recent: int) -> str:
        if total_count <= 1:
            return "isolated"
        if total_count >= 3 and count_recent >= 2:
            return "persistent"
        return "repeating"

    def _runtime_summary_from_inputs(
        self,
        *,
        run_id: str | None,
        bridge: dict,
        planner: dict,
        events: list[dict],
        reasons: list[dict],
        started_at: str | None = None,
        completed_at: str | None = None,
    ) -> dict:
        latest_reason = reasons[0] if reasons else {}
        bridge_state = str(bridge.get("bridge_state") or "no_decision")
        degraded_flags = list(bridge.get("degraded_flags") or [])
        filled_count = int(bridge.get("filled_count", 0) or 0)
        resolved_run_id = run_id or bridge.get("run_id") or planner.get("run_id")
        operator_state = self._runtime_operator_state(
            bridge_state,
            filled_count=filled_count,
            degraded_flags=degraded_flags,
        )
        return {
            "run_id": resolved_run_id,
            "cycle_id": bridge.get("cycle_id") or planner.get("cycle_id"),
            "bridge_state": bridge_state,
            "operator_state": operator_state,
            "planner_status": str(planner.get("planner_status") or "unknown"),
            "planned_count": int(bridge.get("planned_count", 0) or 0),
            "submitted_count": int(bridge.get("submitted_count", 0) or 0),
            "blocked_count": int(bridge.get("blocked_count", 0) or 0),
            "filled_count": filled_count,
            "event_chain_complete": bool(bridge.get("event_chain_complete", False)),
            "latest_reason_code": str(bridge.get("latest_reason_code") or latest_reason.get("reason_code") or "") or None,
            "latest_reason_summary": str(bridge.get("latest_reason_summary") or latest_reason.get("summary") or "") or None,
            "blocking_component": str(
                bridge.get("blocking_component")
                or (latest_reason.get("details") or {}).get("blocking_component")
                or ""
            ) or None,
            "degraded": bool(degraded_flags),
            "degraded_flags": degraded_flags,
            "operator_message": str(bridge.get("operator_message") or "") or None,
            "generated_at": planner.get("generated_at"),
            "last_transition_at": bridge.get("last_transition_at") or planner.get("generated_at") or utc_now_iso(),
            "last_successful_fill_at": self._latest_event_timestamp(events, event_type="fill_recorded", status="ok"),
            "last_successful_portfolio_update_at": self._latest_event_timestamp(events, event_type="portfolio_updated", status="ok"),
            "last_cycle_completed_at": self._latest_event_timestamp(events, event_type="cycle_completed", status="ok"),
            "timeline": self._timeline_items(events, limit=12),
            "detail_path": f"/execution/runs/{resolved_run_id}" if resolved_run_id else None,
            "started_at": started_at,
            "completed_at": completed_at,
        }

    @staticmethod
    def _matches_runtime_run_filters(
        row: dict,
        *,
        operator_state: str | None,
        bridge_state: str | None,
        issue_code: str | None,
        reason_code: str | None,
        blocking_component: str | None,
        degraded: bool | None,
        event_chain_complete: bool | None,
        artifact_available: bool | None,
    ) -> bool:
        if operator_state and str(row.get("operator_state") or "") != operator_state:
            return False
        if bridge_state and str(row.get("bridge_state") or "") != bridge_state:
            return False
        if issue_code and str(((row.get("diagnosis") or {}).get("primary_code") if isinstance(row.get("diagnosis"), dict) else row.get("diagnosis_code")) or "") != issue_code:
            return False
        if reason_code and str(row.get("latest_reason_code") or "") != reason_code:
            return False
        if blocking_component and str(row.get("blocking_component") or "") != blocking_component:
            return False
        if degraded is not None and bool(row.get("degraded")) is not degraded:
            return False
        if event_chain_complete is not None and bool(row.get("event_chain_complete")) is not event_chain_complete:
            return False
        if artifact_available is not None and bool(row.get("artifact_available")) is not artifact_available:
            return False
        return True

    async def get_overview(self) -> dict:
        dashboard = await self.dashboard_service.get_overview()
        execution = await self.analytics_service.execution_summary_live()
        system = await self.monitoring_service.get_system()
        risk = await self.risk_service.get_snapshot()
        alerts = self.alert_service.list_alerts()
        jobs = self.scheduler_service.list_jobs()
        return {
            "status": "ok",
            "portfolio_value": float(dashboard.get("portfolio_value", 0.0) or 0.0),
            "pnl": float(dashboard.get("pnl", 0.0) or 0.0),
            "gross_exposure": float(dashboard.get("gross_exposure", 0.0) or 0.0),
            "net_exposure": float(dashboard.get("net_exposure", 0.0) or 0.0),
            "active_strategies": int(dashboard.get("active_strategies", 0) or 0),
            "open_alerts": int(alerts.get("open_count", alerts.get("count", 0)) or 0),
            "scheduler_jobs": len(jobs),
            "fill_rate": float(execution.get("fill_rate", 0.0) or 0.0),
            "avg_slippage_bps": float(execution.get("avg_slippage_bps", 0.0) or 0.0),
            "system_status": str(system.get("status", "unknown") or "unknown"),
            "execution_state": str(system.get("executionState", "") or ""),
            "execution_reason": str(system.get("executionReason", "") or ""),
            "worker_status": str(system.get("worker_status", system.get("workerStatus", "")) or ""),
            "risk_trading_state": str(risk.get("trading_state", "running") or "running"),
            "kill_switch": str(risk.get("kill_switch", "normal") or "normal"),
            "alert_state": str(risk.get("alert_state", risk.get("alert", "unknown")) or "unknown"),
            "as_of": dashboard.get("as_of") or execution.get("as_of") or system.get("as_of") or utc_now_iso(),
        }

    async def get_strategies(self) -> dict:
        registry = await self.v12_client.get_strategy_registry()
        risk_budget = await self.v12_client.get_strategy_risk_budget()
        risk_by_strategy = {
            str(row.get("strategy_id")): float(row.get("budget_usage", 0.0) or 0.0)
            for row in (risk_budget.get("risk") or {}).get("per_strategy", [])
        }
        runtime_by_strategy = {row["strategy_id"]: row for row in self.analytics_repository.runtime_states()}
        overrides_by_strategy = {row["strategy_id"]: row for row in self.analytics_repository.strategy_overrides()}
        items = []
        for row in registry.get("strategies", []):
            strategy_id = str(row.get("strategy_id", row.get("strategy_name", "unknown")))
            runtime = runtime_by_strategy.get(strategy_id, {})
            override = overrides_by_strategy.get(strategy_id, {})
            items.append(
                {
                    "strategy_id": strategy_id,
                    "strategy_name": str(row.get("strategy_name", strategy_id)),
                    "capital_weight": float(override.get("capital_allocation", row.get("capital_weight", 0.0)) or 0.0),
                    "realized_return": float(row.get("realized_return", row.get("expected_return", 0.0)) or 0.0),
                    "risk_budget_usage": risk_by_strategy.get(strategy_id, 0.0),
                    "risk_budget": override.get("risk_budget"),
                    "status": str(runtime.get("desired_state", "enabled") or "enabled"),
                    "remote_status": str(runtime.get("remote_status", "unknown") or "unknown"),
                    "updated_at": runtime.get("updated_at") or override.get("updated_at") or registry.get("as_of") or utc_now_iso(),
                }
            )
        return {
            "status": "ok",
            "enabled_count": int(registry.get("enabled_count", len(items)) or len(items)),
            "items": items,
            "as_of": registry.get("as_of") or risk_budget.get("as_of") or utc_now_iso(),
        }

    async def get_execution_latest(self) -> dict:
        latest = await self.analytics_service.execution_summary_live()
        return {
            "status": "ok",
            "order_count": int(latest.get("order_count", 0) or 0),
            "fill_count": int(latest.get("fill_count", 0) or 0),
            "fill_rate": float(latest.get("fill_rate", 0.0) or 0.0),
            "avg_slippage_bps": float(latest.get("avg_slippage_bps", 0.0) or 0.0),
            "latency_ms_p50": float(latest.get("latency_ms_p50", 0.0) or 0.0),
            "latency_ms_p95": float(latest.get("latency_ms_p95", 0.0) or 0.0),
            "venue_score": float(latest.get("venue_score", 0.0) or 0.0),
            "as_of": latest.get("as_of") or utc_now_iso(),
        }

    async def get_runtime_latest(self) -> dict:
        bridge, planner, events_payload, reasons_payload = await asyncio.gather(
            self.v12_client.get_execution_bridge_latest(),
            self.v12_client.get_execution_plans_latest(),
            self.v12_client.get_runtime_events_latest(limit=20),
            self.v12_client.get_runtime_reasons_latest(limit=10),
        )
        events = events_payload.get("items", []) if isinstance(events_payload.get("items"), list) else []
        reasons = reasons_payload.get("items", []) if isinstance(reasons_payload.get("items"), list) else []
        summary = self._runtime_summary_from_inputs(
            run_id=bridge.get("run_id") or planner.get("run_id"),
            bridge=bridge,
            planner=planner,
            events=events,
            reasons=reasons,
        )
        return {
            "status": str(bridge.get("status") or "ok"),
            **summary,
            "debug_path": f"/api/v1/command-center/debug/runtime?run_id={bridge.get('run_id')}" if bridge.get("run_id") else "/api/v1/command-center/debug/runtime",
        }

    async def get_runtime_debug(self, run_id: str | None = None) -> dict:
        bridge_task = self.v12_client.get_execution_bridge_by_run(run_id) if run_id else self.v12_client.get_execution_bridge_latest()
        planner_task = self.v12_client.get_execution_plans_by_run(run_id) if run_id else self.v12_client.get_execution_plans_latest()
        events_task = self.v12_client.get_runtime_events_by_run(run_id, limit=50) if run_id else self.v12_client.get_runtime_events_latest(limit=50)
        reasons_task = self.v12_client.get_runtime_reasons_by_run(run_id, limit=20) if run_id else self.v12_client.get_runtime_reasons_latest(limit=20)
        bridge, planner, events_payload, reasons_payload = await asyncio.gather(
            bridge_task,
            planner_task,
            events_task,
            reasons_task,
        )
        resolved_run_id = run_id or bridge.get("run_id") or planner.get("run_id")
        events = [item for item in (events_payload.get("items") or []) if not resolved_run_id or item.get("run_id") == resolved_run_id]
        reasons = reasons_payload.get("items") or []
        run = await self.v12_client.get_runtime_run(resolved_run_id) if resolved_run_id else {}
        run_item = run.get("item") if isinstance(run.get("item"), dict) else run
        artifact_bundle = self._artifact_bundle_for_run(resolved_run_id)
        summary = self._runtime_summary_from_inputs(
            run_id=resolved_run_id,
            bridge=bridge,
            planner=planner,
            events=events,
            reasons=reasons,
            started_at=run_item.get("started_at") or run_item.get("created_at"),
            completed_at=run_item.get("finished_at"),
        )
        artifacts = {
            "bundle": artifact_bundle,
            "checkpoint_count": len(run_item.get("checkpoints") or []),
            "audit_log_count": len(run_item.get("audit_logs") or []),
            "available": [
                name
                for name, present in (
                    ("runtime_bundle", artifact_bundle is not None),
                    ("checkpoints", bool(run_item.get("checkpoints"))),
                    ("audit_logs", bool(run_item.get("audit_logs"))),
                )
                if present
            ],
            "missing": [
                name
                for name, present in (
                    ("runtime_bundle", artifact_bundle is not None),
                    ("checkpoints", bool(run_item.get("checkpoints"))),
                    ("audit_logs", bool(run_item.get("audit_logs"))),
                )
                if not present
            ],
        }
        stages = self._runtime_stage_items(
            run=run_item if isinstance(run_item, dict) else {},
            planner=planner,
            bridge=bridge,
            events=events,
            reasons=reasons,
            artifact_bundle=artifact_bundle,
        )
        diagnosis = self._classify_runtime_diagnosis(summary=summary, stages=stages, artifacts=artifacts)
        recurrence = None
        if diagnosis.get("primary_code"):
            issues_payload = await self.get_runtime_issues(limit=25)
            for item in issues_payload.get("items", []):
                if str(item.get("code") or "") == str(diagnosis.get("primary_code") or ""):
                    recurrence = {
                        "seen_in_recent_runs": f"{int(item.get('distinct_run_count', 0) or 0)} of last {int(item.get('window_run_count', 0) or 0)} runs",
                        "recurrence_status": item.get("recurrence_status"),
                        "trend": item.get("trend"),
                        "first_seen_at": item.get("first_seen_at"),
                        "last_seen_at": item.get("last_seen_at"),
                    }
                    break
        return {
            "scope": "command_center.runtime",
            "status": "ok" if resolved_run_id else "no_data",
            "source": "live" if resolved_run_id else "empty",
            "reason": None if resolved_run_id else "runtime_unavailable",
            "as_of": bridge.get("last_transition_at") or planner.get("generated_at") or utc_now_iso(),
            "timings": {
                "snapshot_age_sec": self._snapshot_age_sec(bridge.get("last_transition_at") or planner.get("generated_at")),
            },
            "summary": summary,
            "provenance": {
                "run_id": resolved_run_id,
                "cycle_id": bridge.get("cycle_id") or planner.get("cycle_id"),
                "upstream_dependencies": [
                    "v12:/execution/plans/latest",
                    "v12:/execution/bridge/latest",
                    "v12:/runtime/events/latest",
                    "v12:/runtime/reasons/latest",
                    "v12:/runtime/runs/{run_id}",
                ],
                "debug_linkage": "planner_truth + bridge_diagnostics + runtime_events + runtime_reasons",
                "artifact_bundle": artifact_bundle,
            },
            "counts": {
                "planner_rows": len(planner.get("items") or []),
                "event_rows": len(events),
                "reason_rows": len(reasons),
                "checkpoint_rows": len(run_item.get("checkpoints") or []),
                "audit_log_rows": len(run_item.get("audit_logs") or []),
            },
            "run": {
                "run_id": resolved_run_id,
                "status": run_item.get("status"),
                "job_name": run_item.get("job_name"),
                "mode": run_item.get("mode"),
                "triggered_by": run_item.get("triggered_by"),
                "started_at": run_item.get("started_at") or run_item.get("created_at"),
                "finished_at": run_item.get("finished_at"),
                "duration_ms": int(run_item.get("duration_ms", 0) or 0),
                "error_message": run_item.get("error_message"),
            },
            "artifacts": artifacts,
            "diagnosis": diagnosis,
            "diagnosis_context": recurrence,
            "stages": stages,
            "timeline": self._timeline_items(events, limit=25),
            "raw": {
                "run": run_item,
                "planner": planner,
                "bridge": bridge,
                "events": events[:25],
                "reasons": reasons[:15],
            },
        }

    async def get_runtime_runs(
        self,
        *,
        limit: int = 20,
        operator_state: str | None = None,
        bridge_state: str | None = None,
        issue_code: str | None = None,
        reason_code: str | None = None,
        blocking_component: str | None = None,
        degraded: bool | None = None,
        event_chain_complete: bool | None = None,
        artifact_available: bool | None = None,
    ) -> dict:
        fetch_limit = min(max(limit * 3, 20), 100)
        runs_payload = await self.v12_client.get_runtime_runs(limit=fetch_limit)
        run_rows = runs_payload.get("items") if isinstance(runs_payload.get("items"), list) else []
        summaries: list[dict] = []

        async def build_summary(run: dict) -> dict:
            run_id = str(run.get("run_id") or "")
            bridge, planner, events_payload, reasons_payload = await asyncio.gather(
                self.v12_client.get_execution_bridge_by_run(run_id),
                self.v12_client.get_execution_plans_by_run(run_id),
                self.v12_client.get_runtime_events_by_run(run_id, limit=25),
                self.v12_client.get_runtime_reasons_by_run(run_id, limit=10),
            )
            events = events_payload.get("items", []) if isinstance(events_payload.get("items"), list) else []
            reasons = reasons_payload.get("items", []) if isinstance(reasons_payload.get("items"), list) else []
            summary = self._runtime_summary_from_inputs(
                run_id=run_id,
                bridge=bridge,
                planner=planner,
                events=events,
                reasons=reasons,
                started_at=run.get("started_at") or run.get("created_at"),
                completed_at=run.get("finished_at"),
            )
            summary["status"] = str(run.get("status") or bridge.get("status") or "unknown")
            summary["duration_ms"] = int(run.get("duration_ms", 0) or 0)
            summary["error_message"] = str(run.get("error_message") or "") or None
            summary["triggered_by"] = str(run.get("triggered_by") or "") or None
            summary["artifact_available"] = self._artifact_bundle_for_run(run_id) is not None
            stages = self._runtime_stage_items(
                run=run,
                planner=planner,
                bridge=bridge,
                events=events,
                reasons=reasons,
                artifact_bundle=self._artifact_bundle_for_run(run_id),
            )
            artifacts = {
                "bundle": self._artifact_bundle_for_run(run_id),
                "available": ["runtime_bundle"] if self._artifact_bundle_for_run(run_id) is not None else [],
                "missing": [] if self._artifact_bundle_for_run(run_id) is not None else ["runtime_bundle"],
            }
            summary["diagnosis"] = self._classify_runtime_diagnosis(summary=summary, stages=stages, artifacts=artifacts)
            summary["diagnosis_code"] = summary["diagnosis"]["primary_code"]
            return summary

        for result in await asyncio.gather(*(build_summary(run) for run in run_rows)):
            if self._matches_runtime_run_filters(
                result,
                operator_state=operator_state,
                bridge_state=bridge_state,
                issue_code=issue_code,
                reason_code=reason_code,
                blocking_component=blocking_component,
                degraded=degraded,
                event_chain_complete=event_chain_complete,
                artifact_available=artifact_available,
            ):
                summaries.append(result)

        return {
            "status": "ok",
            "count": len(summaries[:limit]),
            "items": summaries[:limit],
            "filters": {
                "limit": limit,
                "operator_state": operator_state,
                "bridge_state": bridge_state,
                "issue_code": issue_code,
                "reason_code": reason_code,
                "blocking_component": blocking_component,
                "degraded": degraded,
                "event_chain_complete": event_chain_complete,
                "artifact_available": artifact_available,
            },
            "as_of": utc_now_iso(),
        }

    async def get_runtime_issues(self, *, limit: int = 25) -> dict:
        runs_payload = await self.get_runtime_runs(limit=limit)
        rows = runs_payload.get("items") if isinstance(runs_payload.get("items"), list) else []
        window_run_count = len(rows)
        ordered_rows = list(rows)
        split_index = max(1, len(ordered_rows) // 2) if ordered_rows else 1
        recent_rows = ordered_rows[:split_index]
        older_rows = ordered_rows[split_index:]
        buckets: dict[str, dict] = {}
        for row in rows:
            diagnosis = row.get("diagnosis") if isinstance(row.get("diagnosis"), dict) else {}
            code = str(diagnosis.get("primary_code") or "unknown_runtime_gap")
            bucket = buckets.setdefault(
                code,
                {
                    "code": code,
                    "count": 0,
                    "severity": diagnosis.get("severity"),
                    "retryability": diagnosis.get("retryability"),
                    "operator_action": diagnosis.get("operator_action"),
                    "likely_component": diagnosis.get("likely_component"),
                    "first_seen_at": row.get("completed_at") or row.get("started_at"),
                    "last_seen_at": row.get("completed_at") or row.get("started_at"),
                    "example_run_id": row.get("run_id"),
                    "trend": "flat",
                    "distinct_run_count": 0,
                    "run_ids": set(),
                },
            )
            bucket["count"] += 1
            candidate_ts = row.get("completed_at") or row.get("started_at")
            if candidate_ts and str(candidate_ts) > str(bucket.get("last_seen_at") or ""):
                bucket["last_seen_at"] = candidate_ts
                bucket["example_run_id"] = row.get("run_id")
            if candidate_ts and str(candidate_ts) < str(bucket.get("first_seen_at") or candidate_ts):
                bucket["first_seen_at"] = candidate_ts
            if row.get("run_id"):
                bucket["run_ids"].add(str(row.get("run_id")))

        for code, bucket in buckets.items():
            recent_count = sum(
                1
                for row in recent_rows
                if str((((row.get("diagnosis") or {}) if isinstance(row.get("diagnosis"), dict) else {}).get("primary_code") or row.get("diagnosis_code") or "")) == code
            )
            older_count = sum(
                1
                for row in older_rows
                if str((((row.get("diagnosis") or {}) if isinstance(row.get("diagnosis"), dict) else {}).get("primary_code") or row.get("diagnosis_code") or "")) == code
            )
            bucket["distinct_run_count"] = len(bucket.pop("run_ids"))
            bucket["recurrence_status"] = self._issue_recurrence_status(int(bucket.get("count", 0) or 0), recent_count)
            bucket["trend"] = self._issue_trend(recent_count, older_count)
            bucket["window_run_count"] = window_run_count
            bucket["window_start"] = ordered_rows[-1].get("started_at") if ordered_rows else None
            bucket["window_end"] = ordered_rows[0].get("completed_at") or ordered_rows[0].get("started_at") if ordered_rows else None

        items = sorted(buckets.values(), key=lambda item: (-int(item.get("count", 0) or 0), str(item.get("code") or "")))
        return {
            "status": "ok",
            "count": len(items),
            "items": items,
            "as_of": runs_payload.get("as_of") or utc_now_iso(),
        }

    async def get_execution_debug(self) -> dict:
        stored = self.analytics_service.execution_summary()
        stored_looks_empty = (
            float(stored.get("fill_rate", 0.0) or 0.0) == 0.0
            and float(stored.get("avg_slippage_bps", 0.0) or 0.0) == 0.0
            and float(stored.get("latency_ms_p50", 0.0) or 0.0) == 0.0
            and float(stored.get("latency_ms_p95", 0.0) or 0.0) == 0.0
            and float(stored.get("venue_score", 0.0) or 0.0) == 0.0
        )
        latest, planner, state, orders_payload, fills_payload = await asyncio.gather(
            self.analytics_service.execution_summary_live(),
            self.analytics_service.latest_execution_planner(),
            self.v12_client.get_execution_state_latest(),
            self.v12_client.get_execution_orders(limit=250),
            self.v12_client.get_execution_fills(limit=250),
        )

        orders = orders_payload.get("items") or orders_payload.get("orders") or []
        fills = fills_payload.get("items") or fills_payload.get("fills") or fills_payload.get("latest_fills") or []
        order_count = int(latest.get("order_count", len(orders)) or len(orders))
        fill_count = int(latest.get("fill_count", len(fills)) or len(fills))

        if not stored_looks_empty:
            read_mode = "stored_summary"
            source = "cache"
        else:
            has_live_metrics = any(
                float(latest.get(key, 0.0) or 0.0) > 0.0
                for key in ("fill_rate", "avg_slippage_bps", "latency_ms_p50", "latency_ms_p95", "venue_score")
            )
            if has_live_metrics:
                read_mode = "live_bridge"
                source = "live"
            else:
                read_mode = "empty_summary"
                source = "empty"

        status = "ok" if source != "empty" else "no_data"
        reason = None
        if read_mode == "live_bridge":
            reason = "stored_summary_empty"
        elif read_mode == "empty_summary":
            reason = "execution_summary_unavailable"

        return {
            "scope": "command_center.execution",
            "status": status,
            "source": source,
            "reason": reason,
            "as_of": latest.get("as_of") or planner.get("as_of") or state.get("as_of") or utc_now_iso(),
            "timings": {
                "snapshot_age_sec": self._snapshot_age_sec(latest.get("as_of") or planner.get("as_of") or state.get("as_of")),
            },
            "summary": {
                "fill_rate": float(latest.get("fill_rate", 0.0) or 0.0),
                "avg_slippage_bps": float(latest.get("avg_slippage_bps", 0.0) or 0.0),
                "latency_ms_p50": float(latest.get("latency_ms_p50", 0.0) or 0.0),
                "latency_ms_p95": float(latest.get("latency_ms_p95", 0.0) or 0.0),
                "venue_score": float(latest.get("venue_score", 0.0) or 0.0),
                "order_count": order_count,
                "fill_count": fill_count,
                "execution_state": str(state.get("execution_state") or planner.get("trading_state") or "unknown"),
                "state_reason": str(state.get("reason") or ((state.get("block_reasons") or [{}])[0].get("code") if state.get("block_reasons") else "") or ""),
            },
            "provenance": {
                "read_mode": read_mode,
                "background_refresh_scheduled": False,
                "stores": ["execution_snapshot", "execution_orders", "execution_fills"],
                "upstream_dependencies": [
                    "v12:/execution/quality/latest",
                    "v12:/execution/planner/latest",
                    "v12:/execution/state/latest",
                    "v12:/execution/orders",
                    "v12:/execution/fills",
                ],
                "summary_source": "analytics_repository.latest_execution" if read_mode == "stored_summary" else "v12.execution_quality.latest",
            },
            "counts": {
                "active_plans": int(planner.get("plan_count", 0) or 0),
                "open_orders": int(state.get("open_order_count", order_count) or order_count),
                "fills_considered": len(fills) if isinstance(fills, list) else 0,
            },
            "raw": {
                "stored_summary": stored,
                "live_summary": latest,
                "planner": planner,
                "execution_state": state,
                "orders": orders[:25] if isinstance(orders, list) else [],
                "fills": fills[:25] if isinstance(fills, list) else [],
            },
        }

    async def get_portfolio_summary(self) -> dict:
        overview = await self.portfolio_service.get_overview()
        return {
            "status": "ok",
            "portfolio_value": float(overview.get("portfolio_value", 0.0) or 0.0),
            "cash": float(overview.get("cash", 0.0) or 0.0),
            "pnl": float(overview.get("pnl", 0.0) or 0.0),
            "drawdown": float(overview.get("drawdown", 0.0) or 0.0),
            "gross_exposure": float(overview.get("gross_exposure", 0.0) or 0.0),
            "net_exposure": float(overview.get("net_exposure", 0.0) or 0.0),
            "long_exposure": float(overview.get("long_exposure", 0.0) or 0.0),
            "short_exposure": float(overview.get("short_exposure", 0.0) or 0.0),
            "leverage": float(overview.get("leverage", 0.0) or 0.0),
            "position_count": len(overview.get("positions", [])),
            "as_of": overview.get("as_of") or utc_now_iso(),
        }

    async def get_risk_summary(self) -> dict:
        snapshot = await self.risk_service.get_snapshot()
        trading_state = self.risk_repository.get_trading_state()
        return {
            "status": "ok",
            "gross_exposure": float(snapshot.get("gross_exposure", 0.0) or 0.0),
            "net_exposure": float(snapshot.get("net_exposure", 0.0) or 0.0),
            "leverage": float(snapshot.get("leverage", 0.0) or 0.0),
            "drawdown": float(snapshot.get("drawdown", 0.0) or 0.0),
            "alert_state": str(snapshot.get("alert_state", "unknown") or "unknown"),
            "risk_limit": snapshot.get("risk_limit", {}) or {},
            "trading_state": str(trading_state.get("trading_state", "running") or "running"),
            "as_of": snapshot.get("as_of") or trading_state.get("as_of") or utc_now_iso(),
        }

    async def get_system_summary(self) -> dict:
        monitoring = await self.monitoring_service.get_system()
        execution = await self.monitoring_service.get_execution()
        alerts = self.alert_service.list_alerts()
        jobs = self.scheduler_service.list_jobs()
        return {
            "status": "ok",
            "system_status": str(monitoring.get("status", "unknown") or "unknown"),
            "execution_status": str(execution.get("status", "unknown") or "unknown"),
            "services": monitoring.get("services", {}) or {},
            "open_alerts": int(alerts.get("open_count", alerts.get("count", 0)) or 0),
            "scheduler_jobs": len(jobs),
            "as_of": monitoring.get("as_of") or execution.get("as_of") or utc_now_iso(),
        }

    def get_system_jobs(self) -> dict:
        jobs = self.scheduler_service.list_jobs()
        return {"status": "ok", "count": len(jobs), "items": jobs, "as_of": utc_now_iso()}

    def get_system_alerts(self) -> dict:
        alerts = self.alert_service.list_alerts()
        alerts.setdefault("status", "ok")
        alerts.setdefault("as_of", utc_now_iso())
        return alerts


    async def start_strategy(self, strategy_id: str) -> dict:
        result = await self.control_service.start_strategy(strategy_id)
        self.audit_repository.log_operator_action(
            action_type="command_center.start_strategy",
            target_type="strategy",
            target_id=strategy_id,
            request_json=str({"strategy_id": strategy_id}),
            result_status=(str(result.get("result", {}).get("status", "queued")) if not result.get("ok") else "ok"),
        )
        return {
            "ok": True,
            "message": f"Strategy {strategy_id} start requested.",
            "action": "start_strategy",
            "target": strategy_id,
            "details": result,
            "as_of": utc_now_iso(),
        }

    async def stop_strategy(self, strategy_id: str) -> dict:
        result = await self.control_service.stop_strategy(strategy_id)
        self.audit_repository.log_operator_action(
            action_type="command_center.stop_strategy",
            target_type="strategy",
            target_id=strategy_id,
            request_json=str({"strategy_id": strategy_id}),
            result_status=(str(result.get("result", {}).get("status", "queued")) if not result.get("ok") else "ok"),
        )
        return {
            "ok": True,
            "message": f"Strategy {strategy_id} stop requested.",
            "action": "stop_strategy",
            "target": strategy_id,
            "details": result,
            "as_of": utc_now_iso(),
        }

    async def update_strategy_risk(self, strategy_id: str, risk_budget: float, note: str | None = None) -> dict:
        override = self.analytics_repository.upsert_strategy_override(strategy_id=strategy_id, risk_budget=risk_budget, note=note)
        self.audit_repository.log_operator_action(
            action_type="command_center.update_strategy_risk",
            target_type="strategy",
            target_id=strategy_id,
            request_json=str({"strategy_id": strategy_id, "risk_budget": risk_budget, "note": note}),
            result_status="ok",
        )
        self.audit_repository.log_action(category="command_center", event_type="update_strategy_risk", payload_json=str(override))
        return {
            "ok": True,
            "message": f"Strategy {strategy_id} risk budget updated to {risk_budget}.",
            "action": "update_strategy_risk",
            "target": strategy_id,
            "details": override,
            "as_of": utc_now_iso(),
        }

    async def pause_risk(self, note: str | None = None) -> dict:
        remote = await self.v12_client.pause_runtime(note or "Paused from Command Center")
        state = self.risk_repository.set_trading_state("paused", note or "Paused from Command Center")
        self.audit_repository.log_operator_action(
            action_type="command_center.pause_trading",
            target_type="risk",
            target_id="global",
            request_json=str({"note": note}),
            result_status="ok",
        )
        self.audit_repository.log_action(category="command_center", event_type="pause_trading", payload_json=str(state))
        self.notification_service.notify_risk_event('warning', 'Global trading paused.', {'state': state})
        return {
            "ok": True,
            "message": "Global trading paused.",
            "action": "pause_trading",
            "target": "global",
            "details": {"risk_state": state, "remote_result": remote},
            "as_of": utc_now_iso(),
        }

    async def resume_risk(self, note: str | None = None) -> dict:
        remote = await self.v12_client.resume_runtime(note or "Resumed from Command Center")
        state = self.risk_repository.set_trading_state("running", note or "Resumed from Command Center")
        self.audit_repository.log_operator_action(
            action_type="command_center.resume_trading",
            target_type="risk",
            target_id="global",
            request_json=str({"note": note}),
            result_status="ok",
        )
        self.audit_repository.log_action(category="command_center", event_type="resume_trading", payload_json=str(state))
        self.notification_service.notify_risk_event('info', 'Global trading resumed.', {'state': state})
        return {
            "ok": True,
            "message": "Global trading resumed.",
            "action": "resume_trading",
            "target": "global",
            "details": {"risk_state": state, "remote_result": remote},
            "as_of": utc_now_iso(),
        }

    async def kill_switch(self, note: str | None = None) -> dict:
        result = await self.control_service.kill_switch()
        state = self.risk_repository.set_trading_state("halted", note or "Kill switch triggered from Command Center")
        self.audit_repository.log_kill_switch(status="triggered", note=note or "Command Center kill switch")
        self.notification_service.notify_risk_event('critical', 'Kill switch triggered.', {'note': note, 'state': state})
        self.audit_repository.log_operator_action(
            action_type="command_center.kill_switch",
            target_type="risk",
            target_id="global",
            request_json=str({"note": note}),
            result_status="triggered",
        )
        return {
            "ok": True,
            "message": "Kill switch triggered. Trading moved to halted state.",
            "action": "kill_switch",
            "target": "global",
            "details": {"risk_state": state, "control_result": result},
            "as_of": utc_now_iso(),
        }


    def get_hardening_status(self) -> dict:
        channels = self.notification_service.get_channels()
        return {
            'status': 'ok',
            'rbac_enabled': True,
            'audit_enabled': True,
            'notification_channels': channels,
            'operator_actions_logged': len(self.audit_repository.list_operator_actions()),
            'kill_switch_events': len(self.audit_repository.list_kill_switch_events()),
            'recent_audit_events': len(self.audit_repository.list_audit_logs()),
            'as_of': utc_now_iso(),
        }

    def get_audit_summary(self) -> dict:
        return {
            'status': 'ok',
            'audit_logs': self.audit_repository.list_audit_logs(),
            'operator_actions': self.audit_repository.list_operator_actions(),
            'config_changes': self.audit_repository.list_config_changes(),
            'mode_switches': self.audit_repository.list_mode_switches(),
            'kill_switch_events': self.audit_repository.list_kill_switch_events(),
            'as_of': utc_now_iso(),
        }
