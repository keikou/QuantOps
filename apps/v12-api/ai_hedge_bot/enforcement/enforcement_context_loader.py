from __future__ import annotations


class EnforcementContextLoader:
    def __init__(self, store) -> None:
        self.store = store

    def load(self, approval_id: str = "", target_id: str = "") -> dict:
        governance_state = self.store.fetchone_dict("SELECT * FROM governance_state ORDER BY created_at DESC LIMIT 1") or {}
        risk_state = self.store.fetchone_dict("SELECT * FROM operational_risk_state ORDER BY created_at DESC LIMIT 1") or {}
        safe_mode = self.store.fetchone_dict("SELECT * FROM runtime_safe_mode_state ORDER BY created_at DESC LIMIT 1") or {}
        approval = {}
        if approval_id:
            approval = self.store.fetchone_dict("SELECT * FROM pending_approvals WHERE approval_id=? LIMIT 1", [approval_id]) or {}
        elif target_id:
            approval = self.store.fetchone_dict(
                "SELECT * FROM pending_approvals WHERE target_id=? ORDER BY created_at DESC LIMIT 1",
                [target_id],
            ) or {}
        return {
            "governance_mode": governance_state.get("global_mode", "NORMAL"),
            "orc_risk_level": risk_state.get("global_risk_level") or governance_state.get("last_orc_risk_level") or "L0_NORMAL",
            "execution_mode": safe_mode.get("safe_mode") or safe_mode.get("mode") or "normal",
            "approval_status": approval.get("status", ""),
            "approval": approval,
            "lcc_available": True,
            "lcc_allows_increase": True,
            "lcc_confirms_risk_reduction": True,
            "execution_state_available": True,
            "audit_available": True,
            "hard_safety_flag": False,
        }

