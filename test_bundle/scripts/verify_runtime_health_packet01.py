from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = REPO_ROOT / "apps" / "v12-api"
PLAN_DOC = REPO_ROOT / "docs" / "System_reliability_runtime_hardening_packet01_plan.md"
SYSTEM_ROUTE = APP_ROOT / "ai_hedge_bot" / "api" / "routes" / "system.py"
RUNTIME_STORE = APP_ROOT / "ai_hedge_bot" / "data" / "storage" / "runtime_store.py"
DESIGN_DOCS = [
    REPO_ROOT / "docs" / "04_tasks" / "srh_01_runtime_health_degradation_control_design.md",
    REPO_ROOT / "docs" / "04_tasks" / "srh_01_runtime_health_model_design.md",
    REPO_ROOT / "docs" / "04_tasks" / "srh_01_degradation_detection_control_workflow.md",
    REPO_ROOT / "docs" / "04_tasks" / "srh_01_github_issue_breakdown.md",
    REPO_ROOT / "docs" / "04_tasks" / "srh_lane_boundary_after_afg_freeze.md",
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
    from ai_hedge_bot.runtime_health.health_evaluator import RuntimeHealthEvaluator
    from ai_hedge_bot.runtime_health.degradation_detector import DegradationDetector
    from ai_hedge_bot.runtime_health.control_engine import RuntimeControlEngine
    from ai_hedge_bot.runtime_health.models import ControlActionType, HealthComponent, HealthSignal, HealthSignalType, SeverityLevel
    from ai_hedge_bot.runtime_health.service import RuntimeHealthService

    evaluator = RuntimeHealthEvaluator()
    healthy = evaluator.evaluate_system(
        [
            HealthSignal(HealthComponent.DATA_FEED, HealthSignalType.DATA_FRESHNESS_SEC, 1.0, "verifier"),
            HealthSignal(HealthComponent.EXECUTION, HealthSignalType.LATENCY_MS, 50.0, "verifier"),
            HealthSignal(HealthComponent.RISK, HealthSignalType.ERROR_RATE, 0.0, "verifier"),
        ]
    )
    if healthy.severity != SeverityLevel.S0 or healthy.system_score < 0.90:
        failures.append("runtime:healthy_case_not_s0")

    degraded = evaluator.evaluate_system(
        [
            HealthSignal(HealthComponent.DATA_FEED, HealthSignalType.DATA_FRESHNESS_SEC, 500.0, "verifier"),
            HealthSignal(HealthComponent.EXECUTION, HealthSignalType.EXECUTION_FAILURE_RATE, 0.08, "verifier"),
            HealthSignal(HealthComponent.INFRA, HealthSignalType.HEARTBEAT_AGE_SEC, 260.0, "verifier"),
        ]
    )
    if degraded.severity not in {SeverityLevel.S2, SeverityLevel.S3, SeverityLevel.S4}:
        failures.append(f"runtime:degraded_case_wrong_severity:{degraded.severity}")
    events = DegradationDetector().detect(degraded)
    if not events:
        failures.append("runtime:no_degradation_events")
    actions = [RuntimeControlEngine().action_for_event(event) for event in events]
    if not any(action.action_type in {ControlActionType.PARTIAL_THROTTLE, ControlActionType.SAFE_MODE, ControlActionType.HALT} for action in actions):
        failures.append("runtime:no_control_action")

    service = RuntimeHealthService()
    before_afg = service.store.fetchone_dict("SELECT COUNT(*) AS count FROM governance_audit_bundles") or {"count": 0}
    result = service.ingest_and_evaluate(
        [
            HealthSignal(HealthComponent.DATA_FEED, HealthSignalType.DATA_FRESHNESS_SEC, 700.0, "verifier"),
            HealthSignal(HealthComponent.EXECUTION, HealthSignalType.LATENCY_MS, 6000.0, "verifier"),
        ]
    )
    after_afg = service.store.fetchone_dict("SELECT COUNT(*) AS count FROM governance_audit_bundles") or {"count": 0}
    if before_afg.get("count") != after_afg.get("count"):
        failures.append("runtime:srh_mutated_afg_audit_table")
    if not result.get("degradation_events") or not result.get("control_actions") or not result.get("recovery_attempts"):
        failures.append("runtime:persistence_result_incomplete")
    if service.latest().get("status") != "ok":
        failures.append("runtime:latest_health_failed")
    if not service.trigger_safe_mode("verifier_safe_mode").get("control_action"):
        failures.append("runtime:safe_mode_trigger_failed")


def main() -> None:
    failures: list[str] = []
    endpoints = [
        "/system/runtime-health/ingest",
        "/system/runtime-health/latest",
        "/system/runtime-health/components",
        "/system/runtime-health/signals/latest",
        "/system/degradation/latest",
        "/system/runtime-control/actions/latest",
        "/system/control/safe-mode",
        "/system/runtime-recovery/latest",
    ]
    tables = [
        "runtime_health_signals",
        "runtime_health_snapshots",
        "runtime_health_scores",
        "runtime_degradation_events",
        "runtime_control_actions",
        "runtime_recovery_attempts",
    ]
    modules = [
        "RuntimeHealthService",
        "RuntimeHealthEvaluator",
        "DegradationDetector",
        "RuntimeControlEngine",
        "RecoveryManager",
        "HealthCollector",
    ]
    _contains(PLAN_DOC, endpoints, failures, "plan_missing")
    _contains(SYSTEM_ROUTE, endpoints + ["RuntimeHealthService"], failures, "route_missing")
    _contains(RUNTIME_STORE, tables, failures, "schema_missing")
    for path in DESIGN_DOCS:
        _contains(path, ["SRH-01"], failures, "design_missing")
    module_dir = APP_ROOT / "ai_hedge_bot" / "runtime_health"
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

