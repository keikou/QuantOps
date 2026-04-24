from __future__ import annotations

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_run_id
from ai_hedge_bot.operational_risk.anomaly_detector import AnomalyDetector
from ai_hedge_bot.operational_risk.global_kill_interface import GlobalKillInterface
from ai_hedge_bot.operational_risk.incident_classifier import IncidentClassifier
from ai_hedge_bot.operational_risk.override_manager import OverrideManager
from ai_hedge_bot.operational_risk.response_policy_engine import ResponsePolicyEngine
from ai_hedge_bot.operational_risk.response_orchestrator import RiskResponseOrchestrator
from ai_hedge_bot.operational_risk.risk_metric_engine import RiskMetricEngine
from ai_hedge_bot.operational_risk.risk_state_engine import RiskStateEngine
from ai_hedge_bot.operational_risk.telemetry_loader import TelemetryLoader


class OperationalRiskService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.telemetry = TelemetryLoader()
        self.metrics = RiskMetricEngine()
        self.anomalies = AnomalyDetector()
        self.incidents = IncidentClassifier()
        self.state = RiskStateEngine()
        self.response = ResponsePolicyEngine()
        self.orchestrator = RiskResponseOrchestrator()
        self.global_kill = GlobalKillInterface()
        self.overrides = OverrideManager()

    def _latest_run(self) -> dict:
        return self.store.fetchone_dict(
            """
            SELECT *
            FROM operational_risk_runs
            ORDER BY completed_at DESC, started_at DESC
            LIMIT 1
            """
        ) or {}

    def _latest_rows(self, table: str, limit: int = 100) -> list[dict]:
        return self.store.fetchall_dict(
            f"""
            SELECT *
            FROM {table}
            ORDER BY created_at DESC
            LIMIT ?
            """,
            [max(int(limit), 1)],
        )

    def run(self, limit: int = 50) -> dict:
        run_id = new_run_id()
        started_at = utc_now_iso()
        telemetry = self.telemetry.load()
        metric_rows = self.metrics.compute(telemetry)
        anomaly_rows = self.anomalies.detect(metric_rows)
        incident_rows = self.incidents.classify(anomaly_rows)
        state_row = self.state.compute(incident_rows)
        response_row = self.response.build(state_row, incident_id=incident_rows[0]["incident_type"] if incident_rows else None)
        now = utc_now_iso()

        persisted_metrics = [{**row, "run_id": run_id, "created_at": now} for row in metric_rows]
        persisted_anomalies = [{**row, "anomaly_id": new_run_id(), "run_id": run_id, "created_at": now} for row in anomaly_rows]
        persisted_incidents = [{**row, "incident_id": new_run_id(), "run_id": run_id, "created_at": now} for row in incident_rows]
        persisted_state = {**state_row, "state_id": new_run_id(), "run_id": run_id, "created_at": now}
        persisted_response = {**response_row, "action_id": new_run_id(), "run_id": run_id, "created_at": now, "executed_at": None}

        self.store.append("operational_risk_metrics", persisted_metrics)
        if persisted_anomalies:
            self.store.append("operational_anomalies", persisted_anomalies)
        if persisted_incidents:
            self.store.append("operational_incidents", persisted_incidents)
        self.store.append("operational_risk_state", persisted_state)
        self.store.append("risk_response_actions", persisted_response)
        self.store.append(
            "operational_risk_runs",
            {
                "run_id": run_id,
                "started_at": started_at,
                "completed_at": utc_now_iso(),
                "telemetry_points": len(telemetry),
                "anomaly_count": len(persisted_anomalies),
                "incident_count": len(persisted_incidents),
                "max_risk_level": state_row["global_risk_level"],
                "status": "ok",
                "notes": "orc01_operational_risk_control_plane",
            },
        )
        return self.latest(limit=limit)

    def latest(self, limit: int = 20) -> dict:
        run = self._latest_run()
        if not run:
            return self.run(limit=limit)
        state = self.store.fetchone_dict(
            """
            SELECT *
            FROM operational_risk_state
            WHERE run_id=?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [run.get("run_id")],
        ) or {}
        return {
            "status": "ok",
            "run_id": run.get("run_id"),
            "risk_state": state,
            "operational_risk_summary": {
                "telemetry_points": run.get("telemetry_points"),
                "anomaly_count": run.get("anomaly_count"),
                "incident_count": run.get("incident_count"),
                "max_risk_level": run.get("max_risk_level"),
                "system_operational_risk_action": state.get("recommended_action"),
            },
            "as_of": run.get("completed_at"),
        }

    def risk_state_latest(self) -> dict:
        return self.latest(limit=20)

    def global_risk_metrics_latest(self, limit: int = 20) -> dict:
        self.latest(limit=limit)
        rows = self._latest_rows("operational_risk_metrics", limit=max(limit * 3, 30))
        return {"status": "ok", "items": rows[:limit], "global_risk_metric_summary": {"metric_count": len(rows[:limit])}}

    def anomaly_detection_latest(self, limit: int = 20) -> dict:
        self.latest(limit=limit)
        rows = self._latest_rows("operational_anomalies", limit=max(limit * 3, 30))
        return {"status": "ok", "items": rows[:limit], "anomaly_detection_summary": {"anomaly_count": len(rows[:limit])}}

    def operational_incidents_latest(self, limit: int = 20) -> dict:
        self.latest(limit=limit)
        rows = self._latest_rows("operational_incidents", limit=max(limit * 3, 30))
        return {"status": "ok", "items": rows[:limit], "operational_incident_summary": {"incident_count": len(rows[:limit])}}

    def risk_response_latest(self, limit: int = 20) -> dict:
        self.latest(limit=limit)
        rows = self._latest_rows("risk_response_actions", limit=max(limit * 3, 30))
        return {"status": "ok", "items": rows[:limit], "risk_response_summary": {"action_count": len(rows[:limit])}}

    def execute_response(self, action_id: str = "latest", approved: bool = False) -> dict:
        action = self.store.fetchone_dict(
            """
            SELECT *
            FROM risk_response_actions
            ORDER BY created_at DESC
            LIMIT 1
            """
        ) or {}
        execution = {
            "action_id": action.get("action_id", action_id),
            "requested_action_id": action_id,
            "approved": approved,
            "executed": bool(approved),
            "execution_status": "executed" if approved else "approval_required",
            "executed_at": utc_now_iso(),
        }
        return {"status": "ok", "execution": execution, "source_action": action}

    def trigger_global_kill(
        self,
        trigger_reason: str = "operator_requested",
        risk_level: str = "L5_GLOBAL_HALT",
        kill_scope: str = "global",
        operator_id: str = "operator",
    ) -> dict:
        run = self._latest_run()
        row = self.global_kill.build_event(
            run_id=str(run.get("run_id") or ""),
            trigger_source="operator_manual_trigger",
            trigger_reason=trigger_reason,
            risk_level=risk_level,
            kill_scope=kill_scope,
            operator_id=operator_id,
        )
        row["created_at"] = utc_now_iso()
        self.store.append("global_kill_switch_events", row)
        return {"status": "ok", "global_kill_switch_event": row}

    def global_kill_switch_latest(self, limit: int = 20) -> dict:
        rows = self._latest_rows("global_kill_switch_events", limit=max(limit * 3, 30))
        return {"status": "ok", "items": rows[:limit], "global_kill_switch_summary": {"event_count": len(rows[:limit])}}

    def override(self, operator_id: str = "operator", override_scope: str = "system", override_reason: str = "manual_override") -> dict:
        row = self.overrides.build(operator_id=operator_id, override_scope=override_scope, override_reason=override_reason)
        row["created_at"] = utc_now_iso()
        self.store.append("operational_risk_overrides", row)
        return {"status": "ok", "override": row}

    def orchestrate_response(self) -> dict:
        self.latest(limit=20)
        risk_state = self.store.fetchone_dict(
            """
            SELECT *
            FROM operational_risk_state
            ORDER BY created_at DESC
            LIMIT 1
            """
        ) or {}
        kill_event = self.store.fetchone_dict(
            """
            SELECT *
            FROM global_kill_switch_events
            ORDER BY created_at DESC
            LIMIT 1
            """
        ) or {}
        orchestration = self.orchestrator.orchestrate(risk_state=risk_state, kill_event=kill_event or None)
        now = utc_now_iso()
        row = {
            "orchestration_id": orchestration["orchestration_id"],
            "run_id": risk_state.get("run_id"),
            "event_id": (kill_event or {}).get("event_id"),
            "risk_level": orchestration["risk_level"],
            "scope": orchestration["scope"],
            "recommended_action": orchestration["recommended_action"],
            "requires_operator_approval": orchestration["requires_operator_approval"],
            "lcc_payload": orchestration["lcc_payload"],
            "execution_payload": orchestration["execution_payload"],
            "created_at": now,
        }
        safe_mode = {
            "orchestration_id": orchestration["orchestration_id"],
            **orchestration["safe_mode"],
            "created_at": now,
        }
        recovery = {
            "orchestration_id": orchestration["orchestration_id"],
            **self.orchestrator.recovery_readiness(orchestration["risk_level"]),
            "created_at": now,
        }
        self.store.append("risk_response_orchestrations", row)
        self.store.append("runtime_safe_mode_state", safe_mode)
        self.store.append("risk_recovery_readiness", recovery)
        return {"status": "ok", "orchestration": row, "safe_mode": safe_mode, "recovery_readiness": recovery}

    def risk_response_orchestration_latest(self, limit: int = 20) -> dict:
        rows = self._latest_rows("risk_response_orchestrations", limit=max(limit * 3, 30))
        if not rows:
            self.orchestrate_response()
            rows = self._latest_rows("risk_response_orchestrations", limit=max(limit * 3, 30))
        return {"status": "ok", "items": rows[:limit], "risk_response_orchestration_summary": {"orchestration_count": len(rows[:limit])}}

    def runtime_safe_mode_latest(self, limit: int = 20) -> dict:
        rows = self._latest_rows("runtime_safe_mode_state", limit=max(limit * 3, 30))
        if not rows:
            self.orchestrate_response()
            rows = self._latest_rows("runtime_safe_mode_state", limit=max(limit * 3, 30))
        return {"status": "ok", "items": rows[:limit], "runtime_safe_mode_summary": {"safe_mode_count": len(rows[:limit])}}

    def order_permission_matrix_latest(self) -> dict:
        levels = ["L0_NORMAL", "L1_WATCH", "L2_REDUCE", "L3_FREEZE", "L4_PARTIAL_HALT", "L5_GLOBAL_HALT"]
        rows = []
        for level in levels:
            contract = self.orchestrator.safe_mode.build(level, "global", "permission_matrix")
            rows.append(
                {
                    "risk_level": level,
                    "allowed_order_modes": contract["allowed_order_modes"],
                    "blocked_order_modes": contract["blocked_order_modes"],
                }
            )
        return {"status": "ok", "items": rows, "order_permission_matrix_summary": {"risk_level_count": len(rows)}}

    def recovery_readiness_latest(self, limit: int = 20) -> dict:
        rows = self._latest_rows("risk_recovery_readiness", limit=max(limit * 3, 30))
        if not rows:
            self.orchestrate_response()
            rows = self._latest_rows("risk_recovery_readiness", limit=max(limit * 3, 30))
        return {"status": "ok", "items": rows[:limit], "recovery_readiness_summary": {"recovery_check_count": len(rows[:limit])}}

    def request_risk_recovery(self, operator_id: str = "operator", reason: str = "operator_recovery_request") -> dict:
        readiness = self.recovery_readiness_latest(limit=1)
        latest = (readiness.get("items") or [{}])[0]
        row = {
            "recovery_request_id": new_run_id(),
            "orchestration_id": latest.get("orchestration_id"),
            "operator_id": operator_id,
            "reason": reason,
            "approved": bool(latest.get("ready")),
            "request_status": "approved_for_step_down" if latest.get("ready") else "blocked_pending_readiness",
            "created_at": utc_now_iso(),
        }
        self.store.append("risk_recovery_requests", row)
        return {"status": "ok", "recovery_request": row}
