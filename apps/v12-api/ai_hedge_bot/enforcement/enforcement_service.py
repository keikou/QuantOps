from __future__ import annotations

import json

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_run_id
from ai_hedge_bot.enforcement.consistency_validator import ConsistencyValidator
from ai_hedge_bot.enforcement.enforcement_context_loader import EnforcementContextLoader
from ai_hedge_bot.enforcement.hard_safety_lock import HardSafetyLock
from ai_hedge_bot.enforcement.lifecycle_guard import LifecycleGuard
from ai_hedge_bot.enforcement.policy_apply_guard import PolicyApplyGuard
from ai_hedge_bot.enforcement.pre_allocation_guard import PreAllocationGuard
from ai_hedge_bot.enforcement.pre_dispatch_guard import PreDispatchGuard
from ai_hedge_bot.enforcement.pre_execution_guard import PreExecutionGuard
from ai_hedge_bot.enforcement.schemas import RISK_INCREASING_ACTIONS, RISK_INCREASING_ORDER_MODES
from ai_hedge_bot.enforcement.violation_auditor import ViolationAuditor


class EnforcementService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.context = EnforcementContextLoader(self.store)
        self.hard_lock = HardSafetyLock()
        self.consistency = ConsistencyValidator()
        self.pre_dispatch_guard = PreDispatchGuard()
        self.pre_allocation_guard = PreAllocationGuard()
        self.pre_execution_guard = PreExecutionGuard()
        self.lifecycle_guard = LifecycleGuard()
        self.policy_apply_guard = PolicyApplyGuard()
        self.auditor = ViolationAuditor(self.store)

    def check(
        self,
        boundary: str = "pre_dispatch",
        source_system: str = "AFG",
        action_type: str = "review",
        target_type: str = "system",
        target_id: str = "",
        approval_id: str = "",
        order_mode: str = "",
        exposure_delta: float = 0.0,
        dry_run: bool = False,
        idempotency_key: str = "",
        payload_json: str = "{}",
    ) -> dict:
        request = {
            "boundary": boundary,
            "source_system": source_system,
            "action_type": action_type,
            "target_type": target_type,
            "target_id": target_id,
            "approval_id": approval_id,
            "order_mode": order_mode,
            "exposure_delta": exposure_delta,
            "dry_run": dry_run,
            "idempotency_key": idempotency_key or self._idempotency_key(boundary, source_system, action_type, target_type, target_id),
            "payload_json": payload_json,
        }
        context = self.context.load(approval_id=approval_id, target_id=target_id)
        result = self._evaluate(request, context)
        check_row = self.auditor.persist(request, context, result)
        self._persist_constraints(check_row, result)
        self._persist_consistency_state(context, result)
        return {"status": "ok", "enforcement_check": check_row, "result": result}

    def pre_dispatch(self, **kwargs) -> dict:
        return self.check(boundary="pre_dispatch", **kwargs)

    def pre_allocation(self, **kwargs) -> dict:
        return self.check(boundary="pre_allocation", **kwargs)

    def pre_execution(self, **kwargs) -> dict:
        return self.check(boundary="pre_execution", **kwargs)

    def pre_lifecycle(self, **kwargs) -> dict:
        return self.check(boundary="pre_lifecycle", **kwargs)

    def pre_policy_apply(self, **kwargs) -> dict:
        return self.check(boundary="pre_policy_apply", **kwargs)

    def latest(self, limit: int = 20) -> dict:
        rows = self.store.fetchall_dict("SELECT * FROM policy_enforcement_checks ORDER BY created_at DESC LIMIT ?", [max(int(limit), 1)])
        return {"status": "ok", "items": rows, "policy_enforcement_summary": {"check_count": len(rows)}}

    def violations_latest(self, limit: int = 20) -> dict:
        rows = self.store.fetchall_dict("SELECT * FROM policy_enforcement_violations ORDER BY created_at DESC LIMIT ?", [max(int(limit), 1)])
        return {"status": "ok", "items": rows, "policy_enforcement_violation_summary": {"violation_count": len(rows)}}

    def constraints_latest(self, limit: int = 20) -> dict:
        rows = self.store.fetchall_dict("SELECT * FROM runtime_enforcement_constraints ORDER BY created_at DESC LIMIT ?", [max(int(limit), 1)])
        return {"status": "ok", "items": rows, "runtime_enforcement_constraint_summary": {"constraint_count": len(rows)}}

    def state_latest(self, limit: int = 20) -> dict:
        rows = self.store.fetchall_dict("SELECT * FROM enforcement_consistency_state ORDER BY created_at DESC LIMIT ?", [max(int(limit), 1)])
        if not rows:
            self.check(boundary="pre_dispatch", action_type="record_only", target_type="system")
            rows = self.store.fetchall_dict("SELECT * FROM enforcement_consistency_state ORDER BY created_at DESC LIMIT ?", [max(int(limit), 1)])
        return {"status": "ok", "items": rows, "enforcement_state_summary": {"state_count": len(rows)}}

    def _evaluate(self, request: dict, context: dict) -> dict:
        hard = self.hard_lock.check(request, context)
        if hard:
            return {**hard, "constraints": hard.get("constraints", {})}
        consistency_violations = self.consistency.validate(context)
        if consistency_violations and self._risk_increasing(request):
            return {
                "decision": "REQUIRE_RECONCILIATION",
                "reason": "cross_system_consistency_violation_blocks_risk_increase",
                "constraints": {"requires_reconciliation": True},
                "violations": consistency_violations,
            }
        boundary = request.get("boundary", "pre_dispatch")
        if boundary == "pre_dispatch":
            return self.pre_dispatch_guard.check(request, context)
        if boundary == "pre_allocation":
            return self.pre_allocation_guard.check(request, context)
        if boundary == "pre_execution":
            return self.pre_execution_guard.check(request, context)
        if boundary == "pre_lifecycle":
            return self.lifecycle_guard.check(request, context)
        if boundary == "pre_policy_apply":
            return self.policy_apply_guard.check(request, context)
        return {"decision": "BLOCK", "reason": "unknown_enforcement_boundary", "constraints": {}, "violations": [{"type": "unknown_boundary", "severity": "severe", "reason": boundary}]}

    def _persist_constraints(self, check: dict, result: dict) -> None:
        constraints = result.get("constraints") or {}
        if not constraints:
            return
        rows = [
            {
                "constraint_id": new_run_id(),
                "scope": check.get("enforcement_boundary"),
                "target_id": check.get("target_id"),
                "constraint_type": key,
                "constraint_value": json.dumps(value, ensure_ascii=False, default=str),
                "source_system": check.get("source_system"),
                "active": True,
                "reason": result.get("reason"),
                "created_at": utc_now_iso(),
                "expires_at": None,
            }
            for key, value in constraints.items()
        ]
        self.store.append("runtime_enforcement_constraints", rows)

    def _persist_consistency_state(self, context: dict, result: dict) -> None:
        violations = [v for v in result.get("violations", []) if "mismatch" in str(v.get("type", ""))]
        self.store.append(
            "enforcement_consistency_state",
            {
                "state_id": new_run_id(),
                "orc_risk_level": context.get("orc_risk_level"),
                "afg_governance_mode": context.get("governance_mode"),
                "lcc_state": "available" if context.get("lcc_available") else "missing",
                "execution_mode": context.get("execution_mode"),
                "consistent": not violations,
                "inconsistency_reason": "; ".join(str(v.get("reason")) for v in violations),
                "created_at": utc_now_iso(),
            },
        )

    def _risk_increasing(self, request: dict) -> bool:
        action = str(request.get("action_type") or "")
        mode = str(request.get("order_mode") or "")
        return action in RISK_INCREASING_ACTIONS or mode in RISK_INCREASING_ORDER_MODES or float(request.get("exposure_delta") or 0.0) > 0.0

    def _idempotency_key(self, boundary: str, source_system: str, action_type: str, target_type: str, target_id: str) -> str:
        return f"{boundary}:{source_system}:{action_type}:{target_type}:{target_id}"
