from __future__ import annotations

import json
from pathlib import Path
import sys
from uuid import uuid4


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPO_ROOT / "apps" / "v12-api"
PLAN_DOC = REPO_ROOT / "docs" / "Alpha_factory_governance_operator_control_packet05_plan.md"
CONTRACT_DOC = REPO_ROOT / "docs" / "07_interfaces" / "afg_operator_control_contracts.md"
SYSTEM_ROUTE = APP_ROOT / "ai_hedge_bot" / "api" / "routes" / "system.py"
RUNTIME_STORE = APP_ROOT / "ai_hedge_bot" / "data" / "storage" / "runtime_store.py"
DESIGN_DOCS = [
    REPO_ROOT / "docs" / "04_tasks" / "afg_05_governance_replay_audit_evidence_design.md",
    REPO_ROOT / "docs" / "04_tasks" / "afg_05_audit_evidence_bundle_design.md",
    REPO_ROOT / "docs" / "04_tasks" / "afg_05_governance_replay_workflow.md",
    REPO_ROOT / "docs" / "04_tasks" / "afg_05_github_issue_breakdown.md",
    REPO_ROOT / "docs" / "04_tasks" / "afg_lane_freeze_after_afg_05.md",
]
AFG04_TABLES = [
    "postmortem_incidents",
    "postmortem_reviews",
    "postmortem_rca",
    "postmortem_action_items",
    "postmortem_feedback",
    "postmortem_feedback_dispatch",
]


def _contains(path: Path, needles: list[str], failures: list[str], prefix: str) -> None:
    if not path.exists():
        failures.append(f"missing:{path.name}")
        return
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            failures.append(f"{prefix}:{needle}")


def _table_count(store, table: str) -> int:
    row = store.fetchone_dict(f"SELECT COUNT(*) AS count FROM {table}") or {}
    return int(row.get("count") or 0)


def _seed_complete_incident(postmortem) -> tuple[str, list[dict]]:
    suffix = uuid4().hex
    incident = postmortem.ingest(
        source_system="verify_afg05",
        source_event_id=f"verify_afg05_complete_{suffix}",
        severity="S1",
        incident_type="data_integrity",
        affected_scope="feed",
        target_id="feed_primary",
        summary="afg05 replay fixture",
    )["incident"]
    postmortem.review(incident["incident_id"], reviewer_id="codex", findings_json='{"finding":"fixture"}')
    postmortem.rca(incident["incident_id"], root_cause="data_feed_stale", confidence=0.93, approved=True)
    postmortem.actions(
        incident["incident_id"],
        target_system="ORC",
        action_type="threshold_tighten",
        payload_json='{"metric":"stale_data_seconds","recommended_value":120}',
    )
    feedback = postmortem.build_feedback(incident["incident_id"])["items"]
    for item in feedback:
        postmortem.dispatch_feedback(item["feedback_id"])
    return incident["incident_id"], feedback


def _seed_missing_approval_incident(postmortem) -> str:
    suffix = uuid4().hex
    incident = postmortem.ingest(
        source_system="verify_afg05",
        source_event_id=f"verify_afg05_missing_approval_{suffix}",
        severity="S1",
        incident_type="policy_gap",
        affected_scope="policy",
        target_id="policy_gap",
        summary="afg05 missing approval fixture",
    )["incident"]
    postmortem.review(incident["incident_id"], reviewer_id="codex")
    postmortem.rca(incident["incident_id"], root_cause="policy_gap", confidence=0.88, approved=True)
    postmortem.actions(incident["incident_id"], target_system="AFG_POLICY", action_type="policy_rule_add")
    postmortem.build_feedback(incident["incident_id"])
    return incident["incident_id"]


def _runtime_check(failures: list[str]) -> None:
    sys.path.insert(0, str(APP_ROOT))
    from ai_hedge_bot.governance_audit.audit_service import GovernanceAuditService
    from ai_hedge_bot.postmortem_feedback.postmortem_service import PostmortemService

    postmortem = PostmortemService()
    audit = GovernanceAuditService()
    store = audit.store
    incident_id, feedback = _seed_complete_incident(postmortem)
    before_counts = {table: _table_count(store, table) for table in AFG04_TABLES}
    bundle = audit.build_bundle(incident_id).get("audit_bundle", {})
    if not bundle.get("content_hash") or not bundle.get("chain_hash"):
        failures.append("runtime:bundle_hash_missing")
    components = json.loads(bundle.get("content_json") or "{}")
    for key in ["incident", "rca", "action_items", "feedback", "dispatch", "approvals"]:
        if not components.get(key):
            failures.append(f"runtime:bundle_missing_{key}")
    replay = audit.replay_incident(incident_id).get("replay", {})
    if replay.get("status") != "passed":
        failures.append(f"runtime:replay_not_passed:{replay.get('validation_errors')}")
    for trace_key in ["decision_trace", "approval_trace", "feedback_trace", "dispatch_trace"]:
        if not replay.get(trace_key):
            failures.append(f"runtime:missing_{trace_key}")
    after_counts = {table: _table_count(store, table) for table in AFG04_TABLES}
    if before_counts != after_counts:
        failures.append("runtime:replay_mutated_afg04_tables")
    export = audit.export(incident_id).get("export", {})
    if not export.get("export_path") or not Path(export["export_path"]).exists():
        failures.append("runtime:export_missing")

    store.execute(
        "UPDATE governance_audit_bundles SET content_json=? WHERE bundle_id=?",
        ['{"tampered":true}', bundle["bundle_id"]],
    )
    tampered = audit.replay_incident(incident_id).get("replay", {})
    if tampered.get("status") != "failed" or "content_hash_mismatch" not in tampered.get("validation_errors", []):
        failures.append("runtime:tamper_not_detected")

    missing_approval_incident = _seed_missing_approval_incident(postmortem)
    missing_bundle = audit.build_bundle(missing_approval_incident).get("audit_bundle", {})
    missing_replay = audit.replay_incident(missing_approval_incident).get("replay", {})
    if missing_bundle and missing_replay.get("status") != "failed":
        failures.append("runtime:missing_approval_not_failed")
    if not any(str(error).startswith("missing_approval_evidence_for_feedback:") for error in missing_replay.get("validation_errors", [])):
        failures.append("runtime:missing_approval_error_absent")
    if not feedback:
        failures.append("runtime:feedback_fixture_empty")


def main() -> None:
    failures: list[str] = []
    endpoints = [
        "/system/audit/bundle/{incident_id}",
        "/system/audit/replay/{incident_id}",
        "/system/audit/replay/{replay_id}",
        "/system/audit/export/{incident_id}",
        "/system/audit/bundles/latest",
        "/system/audit/replays/latest",
        "/system/audit/exports/latest",
    ]
    tables = [
        "governance_audit_bundles",
        "governance_replay_logs",
        "governance_decision_trace",
        "governance_audit_exports",
    ]
    modules = [
        "AuditBundleBuilder",
        "GovernanceReplayEngine",
        "TraceBuilder",
        "HashVerifier",
        "AuditExportService",
        "GovernanceAuditService",
    ]
    _contains(PLAN_DOC, endpoints, failures, "plan_missing")
    _contains(CONTRACT_DOC, endpoints, failures, "contract_missing")
    _contains(SYSTEM_ROUTE, endpoints + ["GovernanceAuditService"], failures, "route_missing")
    _contains(RUNTIME_STORE, tables, failures, "schema_missing")
    for path in DESIGN_DOCS:
        _contains(path, ["AFG-05"], failures, "design_missing")
    module_dir = APP_ROOT / "ai_hedge_bot" / "governance_audit"
    for module in modules:
        found = any(module in path.read_text(encoding="utf-8") for path in module_dir.glob("*.py"))
        if not found:
            failures.append(f"module_missing:{module}")
    _runtime_check(failures)
    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

