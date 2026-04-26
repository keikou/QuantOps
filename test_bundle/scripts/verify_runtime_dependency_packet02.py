from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPO_ROOT / "apps" / "v12-api"
PLAN_DOC = REPO_ROOT / "docs" / "System_reliability_runtime_hardening_packet02_plan.md"
SYSTEM_ROUTE = APP_ROOT / "ai_hedge_bot" / "api" / "routes" / "system.py"
RUNTIME_STORE = APP_ROOT / "ai_hedge_bot" / "data" / "storage" / "runtime_store.py"
DESIGN_DOCS = [
    REPO_ROOT / "docs" / "04_tasks" / "srh_02_dependency_failure_isolation_circuit_breaker_design.md",
    REPO_ROOT / "docs" / "04_tasks" / "srh_02_dependency_registry_design.md",
    REPO_ROOT / "docs" / "04_tasks" / "srh_02_circuit_breaker_state_machine_design.md",
    REPO_ROOT / "docs" / "04_tasks" / "srh_02_fallback_isolation_workflow_design.md",
    REPO_ROOT / "docs" / "04_tasks" / "srh_02_recovery_probe_design.md",
    REPO_ROOT / "docs" / "04_tasks" / "srh_02_github_issue_breakdown.md",
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

    service = RuntimeDependencyService()
    before_afg = service.store.fetchone_dict("SELECT COUNT(*) AS count FROM governance_audit_bundles") or {"count": 0}

    primary = "verifier_srh02_primary"
    fallback = "verifier_srh02_fallback"
    isolated = "verifier_srh02_isolated"

    reg = service.register_dependency(primary, "DATA_FEED", "Verifier Primary Feed", "srh", "critical", fallback)
    service.register_dependency(fallback, "DATA_FEED", "Verifier Fallback Feed", "srh", "standard")
    if reg.get("circuit_breaker", {}).get("state") != "CLOSED":
        failures.append("runtime:register_did_not_create_closed_circuit")

    success = service.record_success(primary, latency_ms=10.0, detail="healthy_probe")
    if success.get("circuit_breaker", {}).get("state") != "CLOSED":
        failures.append("runtime:success_did_not_keep_closed")

    result = {}
    for _ in range(3):
        result = service.record_failure(primary, "timeout", 5000.0, "dependency_timeout")
    if result.get("circuit_breaker", {}).get("state") != "OPEN":
        failures.append("runtime:failure_threshold_did_not_open")
    if not result.get("fallback_route") or result["fallback_route"].get("fallback_dependency_id") != fallback:
        failures.append("runtime:fallback_route_not_selected")

    half_open = service.half_open_circuit(primary)
    if half_open.get("status") != "ok" or half_open.get("circuit_breaker", {}).get("state") != "HALF_OPEN":
        failures.append("runtime:open_to_half_open_failed")
    probe = service.schedule_probe(primary)
    probe_id = probe.get("recovery_probe", {}).get("probe_id")
    complete = service.complete_probe(probe_id, True, "dependency_recovered")
    if complete.get("circuit_breaker", {}).get("state") != "CLOSED":
        failures.append("runtime:successful_probe_did_not_close")

    blocked = service.half_open_circuit(primary)
    if blocked.get("status") != "blocked" or blocked.get("transition", {}).get("allowed") is not False:
        failures.append("runtime:illegal_transition_not_blocked")

    service.register_dependency(isolated, "EXTERNAL_API", "Verifier External API", "srh", "critical", "")
    for _ in range(3):
        isolated_result = service.record_failure(isolated, "http_503", 0.0, "dependency_unavailable")
    if not isolated_result.get("isolation_event"):
        failures.append("runtime:no_fallback_did_not_isolate")

    service.half_open_circuit(isolated)
    failed_probe = service.schedule_probe(isolated)
    failed_probe_id = failed_probe.get("recovery_probe", {}).get("probe_id")
    failed = service.complete_probe(failed_probe_id, False, "still_unhealthy")
    if failed.get("circuit_breaker", {}).get("state") != "OPEN":
        failures.append("runtime:failed_probe_did_not_reopen")

    latest = service.latest_breakers()
    if latest.get("circuit_breaker_summary", {}).get("breaker_count", 0) < 1:
        failures.append("runtime:latest_breakers_empty")
    if service.latest_fallback_routes().get("fallback_route_summary", {}).get("route_count", 0) < 1:
        failures.append("runtime:latest_fallback_empty")
    if service.latest_isolation().get("dependency_isolation_summary", {}).get("isolation_count", 0) < 1:
        failures.append("runtime:latest_isolation_empty")
    if service.latest_probes().get("recovery_probe_summary", {}).get("probe_count", 0) < 1:
        failures.append("runtime:latest_probes_empty")

    after_afg = service.store.fetchone_dict("SELECT COUNT(*) AS count FROM governance_audit_bundles") or {"count": 0}
    if before_afg.get("count") != after_afg.get("count"):
        failures.append("runtime:srh02_mutated_afg_audit_table")


def main() -> None:
    failures: list[str] = []
    endpoints = [
        "/system/dependencies",
        "/system/dependencies/{dependency_id}",
        "/system/dependencies/register",
        "/system/dependencies/health/latest",
        "/system/dependencies/{dependency_id}/record-success",
        "/system/dependencies/{dependency_id}/record-failure",
        "/system/circuit-breakers/latest",
        "/system/circuit-breakers/{dependency_id}",
        "/system/circuit-breakers/{dependency_id}/open",
        "/system/circuit-breakers/{dependency_id}/half-open",
        "/system/circuit-breakers/{dependency_id}/close",
        "/system/dependency-isolation/latest",
        "/system/fallback-routes/latest",
        "/system/recovery-probes/{dependency_id}/schedule",
        "/system/recovery-probes/{probe_id}/complete",
        "/system/recovery-probes/latest",
    ]
    tables = [
        "runtime_dependency_registry",
        "runtime_dependency_health",
        "runtime_dependency_events",
        "runtime_circuit_breakers",
        "runtime_circuit_transitions",
        "runtime_fallback_routes",
        "runtime_recovery_probes",
    ]
    modules = [
        "RuntimeDependencyService",
        "DependencyRegistration",
        "CircuitBreakerSnapshot",
        "RecoveryProbe",
        "FallbackRoute",
    ]
    _contains(PLAN_DOC, endpoints + tables, failures, "plan_missing")
    _contains(SYSTEM_ROUTE, endpoints + ["RuntimeDependencyService"], failures, "route_missing")
    _contains(RUNTIME_STORE, tables, failures, "schema_missing")
    for path in DESIGN_DOCS:
        _contains(path, ["SRH-02"], failures, "design_missing")
    module_dir = APP_ROOT / "ai_hedge_bot" / "runtime_dependencies"
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
