from __future__ import annotations

import json

from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_run_id


class ViolationAuditor:
    def __init__(self, store) -> None:
        self.store = store

    def persist(self, request: dict, context: dict, result: dict) -> dict:
        now = utc_now_iso()
        check = {
            "check_id": new_run_id(),
            "source_system": request.get("source_system", "unknown"),
            "action_type": request.get("action_type", ""),
            "target_type": request.get("target_type", ""),
            "target_id": request.get("target_id", ""),
            "enforcement_boundary": request.get("boundary", "pre_dispatch"),
            "decision": result["decision"],
            "reason": result["reason"],
            "constraints_json": json.dumps(result.get("constraints", {}), ensure_ascii=False, default=str),
            "context_json": json.dumps(context, ensure_ascii=False, default=str),
            "created_at": now,
        }
        self.store.append("policy_enforcement_checks", check)
        violations = []
        for violation in result.get("violations", []):
            violations.append(
                {
                    "violation_id": new_run_id(),
                    "check_id": check["check_id"],
                    "violation_type": violation.get("type", "policy_violation"),
                    "severity": violation.get("severity", "warning"),
                    "source_system": request.get("source_system", "unknown"),
                    "action_type": request.get("action_type", ""),
                    "target_type": request.get("target_type", ""),
                    "target_id": request.get("target_id", ""),
                    "reason": violation.get("reason", result["reason"]),
                    "evidence_json": json.dumps({"request": request, "context": context}, ensure_ascii=False, default=str),
                    "created_at": now,
                }
            )
        if violations:
            self.store.append("policy_enforcement_violations", violations)
        return check

