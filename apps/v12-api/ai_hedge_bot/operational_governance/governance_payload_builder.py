from __future__ import annotations

import json

from ai_hedge_bot.operational_governance.schemas import APPROVAL_REQUIRED_LEVELS


class GovernancePayloadBuilder:
    def build(self, incident: dict) -> dict:
        risk_level = str(incident.get("risk_level") or "L1_WATCH")
        action = str(incident.get("recommended_action") or self._default_action(risk_level))
        return {
            "source_system": "ORC",
            "source_event_id": incident.get("source_incident_id"),
            "target_type": incident.get("affected_scope") or "system",
            "target_id": incident.get("target_id") or "global",
            "proposed_action": action,
            "risk_level": risk_level,
            "requires_approval": risk_level in APPROVAL_REQUIRED_LEVELS,
            "reason": incident.get("summary") or incident.get("incident_type") or "operational_risk_incident",
            "payload_json": json.dumps(
                {
                    "source_system": incident.get("source_system"),
                    "incident_type": incident.get("incident_type"),
                    "recommended_safe_mode": action,
                },
                ensure_ascii=False,
                default=str,
            ),
        }

    def _default_action(self, risk_level: str) -> str:
        if risk_level == "L5_GLOBAL_HALT":
            return "global_halt"
        if risk_level == "L4_PARTIAL_HALT":
            return "partial_halt"
        if risk_level == "L3_FREEZE":
            return "freeze_new_risk"
        if risk_level == "L2_REDUCE":
            return "reduce_only"
        return "audit_only"

