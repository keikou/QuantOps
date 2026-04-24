from __future__ import annotations

from ai_hedge_bot.core.ids import new_run_id
from ai_hedge_bot.operational_risk.safe_mode_contract import SafeModeContract


class RiskResponseOrchestrator:
    def __init__(self) -> None:
        self.safe_mode = SafeModeContract()

    def orchestrate(self, risk_state: dict, kill_event: dict | None = None) -> dict:
        risk_level = str((kill_event or {}).get("risk_level") or risk_state.get("global_risk_level") or "L1_WATCH")
        scope = str((kill_event or {}).get("kill_scope") or "global")
        reason = str((kill_event or {}).get("trigger_reason") or risk_state.get("reason") or "risk_state_orchestration")
        event_id = str((kill_event or {}).get("event_id") or "")
        safe_mode = self.safe_mode.build(risk_level=risk_level, scope=scope, reason=reason, event_id=event_id)
        return {
            "orchestration_id": new_run_id(),
            "risk_level": risk_level,
            "scope": scope,
            "recommended_action": self._action(risk_level),
            "safe_mode": safe_mode,
            "lcc_payload": self._lcc_payload(risk_level, scope, reason, event_id),
            "execution_payload": self._execution_payload(safe_mode),
            "requires_operator_approval": risk_level in {"L4_PARTIAL_HALT", "L5_GLOBAL_HALT"},
        }

    def recovery_readiness(self, risk_level: str) -> dict:
        required = [
            "incident_resolved",
            "telemetry_healthy",
            "data_fresh",
            "execution_connector_healthy",
            "portfolio_truth_reconciled",
        ]
        if risk_level in {"L4_PARTIAL_HALT", "L5_GLOBAL_HALT"}:
            required.append("operator_approval")
        return {
            "risk_level": risk_level,
            "required_checks": ",".join(required),
            "ready": risk_level in {"L0_NORMAL", "L1_WATCH"},
            "recovery_action": "hold_state_until_checks_pass" if risk_level not in {"L0_NORMAL", "L1_WATCH"} else "normal_monitoring",
        }

    def _action(self, risk_level: str) -> str:
        return {
            "L0_NORMAL": "normal_operation",
            "L1_WATCH": "increase_monitoring",
            "L2_REDUCE": "reduce_exposure_and_order_rate",
            "L3_FREEZE": "freeze_new_exposure_reduce_only",
            "L4_PARTIAL_HALT": "halt_affected_scope",
            "L5_GLOBAL_HALT": "halt_all_new_risk",
        }.get(risk_level, "increase_monitoring")

    def _lcc_payload(self, risk_level: str, scope: str, reason: str, event_id: str) -> str:
        return f"source=ORC;risk_level={risk_level};scope={scope};reason={reason};idempotency_key={scope}:{risk_level}:{event_id}"

    def _execution_payload(self, safe_mode: dict) -> str:
        return (
            f"risk_state={safe_mode['risk_state']};scope={safe_mode['scope']};"
            f"allowed={safe_mode['allowed_order_modes']};blocked={safe_mode['blocked_order_modes']}"
        )

