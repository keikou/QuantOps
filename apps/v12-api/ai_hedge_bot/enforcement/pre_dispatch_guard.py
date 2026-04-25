from __future__ import annotations


class PreDispatchGuard:
    def check(self, request: dict, context: dict) -> dict:
        if bool(request.get("dry_run", False)):
            return {"decision": "DRY_RUN_ONLY", "reason": "dry_run_dispatch_only", "constraints": {}, "violations": []}
        status = str(context.get("approval_status") or "")
        if status in {"rejected", "expired"}:
            return {"decision": "BLOCK", "reason": f"approval_{status}", "constraints": {}, "violations": [{"type": "approval_invalid", "severity": "severe", "reason": status}]}
        if status not in {"approved", "auto_applied", "dry_run"}:
            return {"decision": "REQUIRE_APPROVAL", "reason": "dispatch_requires_approval", "constraints": {}, "violations": []}
        return {"decision": "ALLOW", "reason": "dispatch_allowed", "constraints": {}, "violations": []}

