from __future__ import annotations

import json
from pathlib import Path
import sys
from uuid import uuid4


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPO_ROOT / "apps" / "v12-api"
PLAN_DOC = REPO_ROOT / "docs" / "Alpha_factory_governance_operator_control_packet04_plan.md"
TASK_DOC = REPO_ROOT / "docs" / "04_tasks" / "afg04_incident_review_postmortem_2026-04-26.md"
CONTRACT_DOC = REPO_ROOT / "docs" / "07_interfaces" / "afg_operator_control_contracts.md"
SYSTEM_ROUTE = APP_ROOT / "ai_hedge_bot" / "api" / "routes" / "system.py"
RUNTIME_STORE = APP_ROOT / "ai_hedge_bot" / "data" / "storage" / "runtime_store.py"


def _contains(path: Path, needles: list[str], failures: list[str], prefix: str) -> None:
    if not path.exists():
        failures.append(f"missing:{path.name}")
        return
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            failures.append(f"{prefix}:{needle}")


def _runtime_check(failures: list[str]) -> None:
    sys.path.insert(0, str(APP_ROOT))
    from ai_hedge_bot.postmortem_feedback.postmortem_service import PostmortemService

    service = PostmortemService()
    source_event_id = f"verify_afg04_data_feed_stale_{uuid4().hex}"
    incident = service.ingest(
        source_system="verify_afg04",
        source_event_id=source_event_id,
        severity="S1",
        incident_type="data_integrity",
        affected_scope="feed",
        target_id="feed_primary",
        summary="stale data incident",
    )["incident"]
    blocked = service.close(incident["incident_id"], emit_feedback=False)
    if blocked.get("status") != "blocked":
        failures.append("runtime:high_severity_close_without_rca_not_blocked")

    service.review(incident["incident_id"], reviewer_id="codex", findings_json='{"finding":"stale feed"}')
    service.rca(incident["incident_id"], root_cause="data_feed_stale", confidence=0.91, approved=True)
    service.actions(
        incident["incident_id"],
        target_system="ORC",
        action_type="threshold_tighten",
        payload_json='{"metric":"stale_data_seconds","recommended_value":120}',
    )
    feedback = service.build_feedback(incident["incident_id"])
    items = feedback.get("items", [])
    targets = {item.get("target_system") for item in items}
    if not {"ORC", "AFG_POLICY", "EXECUTION"}.issubset(targets):
        failures.append(f"runtime:missing_feedback_targets:{sorted(targets)}")
    if not all(item.get("requires_approval") for item in items):
        failures.append("runtime:approval_gate_missing")

    first_feedback = items[0]
    dispatch_one = service.dispatch_feedback(first_feedback["feedback_id"]).get("dispatch", {})
    dispatch_two = service.dispatch_feedback(first_feedback["feedback_id"]).get("dispatch", {})
    if dispatch_one.get("dispatch_id") != dispatch_two.get("dispatch_id"):
        failures.append("runtime:dispatch_not_idempotent")
    if dispatch_one.get("dispatch_status") != "pending_approval":
        failures.append("runtime:approval_required_feedback_not_staged")


def main() -> None:
    failures: list[str] = []
    endpoints = [
        "/system/incidents/ingest",
        "/system/incidents/latest",
        "/system/incidents/{id}/review",
        "/system/incidents/{id}/rca",
        "/system/incidents/{id}/actions",
        "/system/incidents/{id}/close",
        "/system/postmortem/latest",
        "/system/postmortem-feedback/build/{incident_id}",
        "/system/postmortem-feedback/dispatch/{feedback_id}",
        "/system/postmortem-feedback/latest",
        "/system/postmortem-feedback/target/{target_system}",
        "/system/postmortem-feedback/dispatch/latest",
    ]
    tables = [
        "postmortem_incidents",
        "postmortem_reviews",
        "postmortem_rca",
        "postmortem_action_items",
        "postmortem_feedback",
        "postmortem_feedback_dispatch",
    ]
    modules = [
        "PostmortemService",
        "FeedbackBuilder",
        "FeedbackDispatcher",
        "AESFeedbackAdapter",
        "ORCFeedbackAdapter",
        "AFGPolicyFeedbackAdapter",
        "LCCFeedbackAdapter",
        "ExecutionFeedbackAdapter",
    ]
    _contains(PLAN_DOC, endpoints, failures, "plan_missing")
    _contains(TASK_DOC, endpoints, failures, "task_missing")
    _contains(CONTRACT_DOC, endpoints, failures, "contract_missing")
    _contains(SYSTEM_ROUTE, endpoints + ["PostmortemService"], failures, "route_missing")
    _contains(RUNTIME_STORE, tables, failures, "schema_missing")
    for module in modules:
        found = any(module in path.read_text(encoding="utf-8") for path in (APP_ROOT / "ai_hedge_bot" / "postmortem_feedback").glob("*.py"))
        if not found:
            failures.append(f"module_missing:{module}")
    _runtime_check(failures)
    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
