from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPO_ROOT / "apps" / "v12-api"
PLAN_DOC = REPO_ROOT / "docs" / "System_reliability_runtime_hardening_packet03_plan.md"
SYSTEM_ROUTE = APP_ROOT / "ai_hedge_bot" / "api" / "routes" / "system.py"
RUNTIME_STORE = APP_ROOT / "ai_hedge_bot" / "data" / "storage" / "runtime_store.py"
DESIGN_DOCS = [
    REPO_ROOT / "docs" / "04_tasks" / "srh_03_runtime_incident_escalation_operator_notification_design.md",
    REPO_ROOT / "docs" / "04_tasks" / "srh_03_escalation_rule_registry_design.md",
    REPO_ROOT / "docs" / "04_tasks" / "srh_03_operator_notification_lifecycle_design.md",
    REPO_ROOT / "docs" / "04_tasks" / "srh_03_afg04_incident_handoff_design.md",
    REPO_ROOT / "docs" / "04_tasks" / "srh_03_dedup_cooldown_escalation_audit_design.md",
    REPO_ROOT / "docs" / "04_tasks" / "srh_03_github_issue_breakdown.md",
]


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
    from ai_hedge_bot.runtime_dependencies.service import RuntimeDependencyService
    from ai_hedge_bot.runtime_escalation.escalation_service import RuntimeEscalationService
    from ai_hedge_bot.runtime_health.models import HealthComponent, HealthSignal, HealthSignalType
    from ai_hedge_bot.runtime_health.service import RuntimeHealthService

    health = RuntimeHealthService()
    deps = RuntimeDependencyService()
    escalation = RuntimeEscalationService()

    before_afg = escalation.store.fetchone_dict("SELECT COUNT(*) AS count FROM governance_audit_bundles") or {"count": 0}

    escalation.register_rule(
        "verifier_srh03_degradation_rule",
        "RUNTIME_DEGRADATION",
        "S3",
        "CRITICAL",
        requires_ack=True,
        handoff_to_afg04=True,
        cooldown_seconds=900,
        dedup_key_template="{source_type}:{source_event_id}:{severity}",
    )
    degraded = health.ingest_and_evaluate(
        [HealthSignal(HealthComponent.INFRA, HealthSignalType.HEARTBEAT_AGE_SEC, 180.0, "srh03_verifier")]
    )
    degradation_event_id = degraded["degradation_events"][0]["event_id"]
    degradation_escalation = escalation.evaluate_degradation(degradation_event_id)
    if degradation_escalation.get("status") != "ok":
        failures.append(f"runtime:degradation_escalation_failed:{degradation_escalation.get('status')}")
    if degradation_escalation.get("notification", {}).get("status") != "ACK_REQUIRED":
        failures.append("runtime:critical_notification_not_ack_required")
    notification_id = degradation_escalation.get("notification", {}).get("notification_id", "")
    ack = escalation.ack_notification(notification_id, "operator.verifier", "investigating")
    if ack.get("notification", {}).get("status") != "ACKED":
        failures.append("runtime:ack_did_not_update_notification")
    handoff = degradation_escalation.get("handoff", {}).get("handoff", {})
    if handoff.get("status") != "INGESTED" or not handoff.get("incident_id"):
        failures.append("runtime:critical_handoff_not_ingested")

    escalation.register_rule(
        "verifier_srh03_dependency_rule",
        "FALLBACK_UNAVAILABLE",
        "S3",
        "CRITICAL",
        requires_ack=True,
        handoff_to_afg04=True,
        cooldown_seconds=900,
        dedup_key_template="{source_type}:{source_event_id}:{severity}",
    )
    dependency_id = "verifier_srh03_no_fallback"
    deps.register_dependency(dependency_id, "EXTERNAL_API", "Verifier No Fallback", "srh", "critical", "")
    dependency_result = {}
    for _ in range(3):
        dependency_result = deps.record_failure(dependency_id, "http_503", 0.0, "dependency_unavailable")
    dependency_event_id = dependency_result.get("isolation_event", {}).get("event_id", "")
    dependency_escalation = escalation.evaluate_dependency(dependency_event_id)
    if dependency_escalation.get("status") != "ok":
        failures.append(f"runtime:dependency_escalation_failed:{dependency_escalation.get('status')}")
    duplicate = escalation.evaluate_dependency(dependency_event_id)
    if duplicate.get("status") != "duplicate_suppressed":
        failures.append("runtime:duplicate_not_suppressed")
    audit_rows = escalation.audit_latest(100).get("items", [])
    if not any(row.get("event_type") == "DUPLICATE_SUPPRESSED" for row in audit_rows):
        failures.append("runtime:duplicate_suppression_not_audited")

    handoff_id = dependency_escalation.get("handoff", {}).get("handoff", {}).get("handoff_id", "")
    failed = escalation.retry_handoff(handoff_id, force_fail=True)
    if failed.get("status") != "failed":
        failures.append("runtime:failed_handoff_not_persisted")

    after_afg = escalation.store.fetchone_dict("SELECT COUNT(*) AS count FROM governance_audit_bundles") or {"count": 0}
    if before_afg.get("count") != after_afg.get("count"):
        failures.append("runtime:srh03_mutated_afg_audit_table")


def main() -> None:
    failures: list[str] = []
    endpoints = [
        "/system/escalation/rules",
        "/system/escalation/rules/register",
        "/system/escalation/evaluate/degradation/{event_id}",
        "/system/escalation/evaluate/dependency/{event_id}",
        "/system/escalations/latest",
        "/system/escalations/{escalation_id}",
        "/system/operator-notifications/latest",
        "/system/operator-notifications/{notification_id}",
        "/system/operator-notifications/{notification_id}/ack",
        "/system/incident-handoffs/latest",
        "/system/incident-handoffs/{handoff_id}",
        "/system/incident-handoffs/{handoff_id}/retry",
        "/system/escalation-audit/latest",
    ]
    tables = [
        "runtime_escalation_rules",
        "runtime_escalation_events",
        "runtime_escalation_dedup",
        "runtime_escalation_audit_log",
        "runtime_operator_notifications",
        "runtime_operator_notification_acks",
        "runtime_operator_notification_delivery",
        "runtime_incident_handoffs",
        "runtime_incident_handoff_attempts",
    ]
    modules = ["RuntimeEscalationService", "EscalationRule", "NotificationStatus", "AuditEventType"]
    _contains(PLAN_DOC, endpoints + tables, failures, "plan_missing")
    _contains(SYSTEM_ROUTE, endpoints + ["RuntimeEscalationService"], failures, "route_missing")
    _contains(RUNTIME_STORE, tables, failures, "schema_missing")
    for path in DESIGN_DOCS:
        _contains(path, ["SRH-03"], failures, "design_missing")
    module_dir = APP_ROOT / "ai_hedge_bot" / "runtime_escalation"
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
