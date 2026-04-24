from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Autonomous_alpha_expansion_strategy_generation_intelligence_packet01_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_aae01_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/alpha-discovery-candidates/latest",
            "/system/alpha-validation-results/latest",
            "/system/alpha-admission-decision/latest",
            "/system/alpha-lifecycle-state/latest",
            "/system/alpha-inventory-health/latest",
            "replacement_pressure",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.autonomous_alpha_expansion_strategy_generation_intelligence_service import (
        AutonomousAlphaExpansionStrategyGenerationIntelligenceService,
    )

    service = AutonomousAlphaExpansionStrategyGenerationIntelligenceService()

    service._latest_registry_rows = lambda limit=200: [
        {
            "alpha_id": "alpha.trend.next",
            "alpha_family": "trend",
            "factor_type": "momentum",
            "horizon": "short",
            "turnover_profile": "medium",
            "feature_dependencies": ["momentum_4", "trend_strength"],
            "state": "candidate",
        },
        {
            "alpha_id": "alpha.carry.shadow",
            "alpha_family": "carry",
            "factor_type": "carry",
            "horizon": "short",
            "turnover_profile": "medium",
            "feature_dependencies": ["funding_rate"],
            "state": "validated",
        },
        {
            "alpha_id": "alpha.event.fail",
            "alpha_family": "event",
            "factor_type": "breakout",
            "horizon": "short",
            "turnover_profile": "high",
            "feature_dependencies": ["volume_spike"],
            "state": "candidate",
        },
    ]
    service._latest_eval_rows = lambda limit=200: [
        {
            "alpha_id": "alpha.trend.next",
            "summary_score": 0.88,
            "decision": "pass",
            "sharpe": 1.5,
            "max_drawdown": 0.08,
            "fill_probability": 0.92,
        },
        {
            "alpha_id": "alpha.carry.shadow",
            "summary_score": 0.73,
            "decision": "shadow",
            "sharpe": 1.12,
            "max_drawdown": 0.1,
            "fill_probability": 0.84,
        },
        {
            "alpha_id": "alpha.event.fail",
            "summary_score": 0.58,
            "decision": "research",
            "sharpe": 0.71,
            "max_drawdown": 0.17,
            "fill_probability": 0.65,
        },
    ]
    service._latest_ranking_rows = lambda limit=200: [
        {"alpha_id": "alpha.trend.next", "rank_score": 0.86},
        {"alpha_id": "alpha.carry.shadow", "rank_score": 0.72},
        {"alpha_id": "alpha.event.fail", "rank_score": 0.41},
    ]
    service._latest_status_rows = lambda limit=200: [
        {"alpha_id": "alpha.trend.next", "event_type": "test", "from_state": "candidate", "to_state": "pass", "reason": "summary_score=0.88"},
        {"alpha_id": "alpha.carry.shadow", "event_type": "shadow", "from_state": "validated", "to_state": "shadow", "reason": "rank_score=0.72"},
        {"alpha_id": "alpha.event.fail", "event_type": "research", "from_state": "candidate", "to_state": "research", "reason": "rank_score=0.41"},
    ]
    service._latest_library_rows = lambda limit=200: [
        {"alpha_id": "alpha.trend.next", "state": "candidate", "tags": ["trend"]},
        {"alpha_id": "alpha.carry.shadow", "state": "shadow", "tags": ["carry"]},
        {"alpha_id": "alpha.event.fail", "state": "research", "tags": ["event"]},
    ]
    service._latest_experiment_rows = lambda limit=200: [
        {"experiment_id": "exp-trend", "alpha_id": "alpha.trend.next"},
    ]
    service._latest_validation_rows = lambda limit=200: [
        {"experiment_id": "exp-trend", "summary_score": 0.87, "passed": True},
    ]
    service._regime_context = lambda limit=20: {
        "current_regime": "transition",
        "regime_confidence": 0.67,
        "family_regime_state": {"trend": "risk_on", "carry": "balanced", "event": "risk_off"},
        "system_regime_action": "observe_regime_shift_and_prepare_gating",
    }

    discovery = service.alpha_discovery_candidates_latest(limit=10)
    validation = service.alpha_validation_results_latest(limit=10)
    admission = service.alpha_admission_decision_latest(limit=10)
    lifecycle = service.alpha_lifecycle_state_latest(limit=10)
    inventory = service.alpha_inventory_health_latest(limit=10)

    if discovery.get("status") != "ok":
        failures.append("discovery_status_not_ok")
    if validation.get("status") != "ok":
        failures.append("validation_status_not_ok")
    if admission.get("status") != "ok":
        failures.append("admission_status_not_ok")
    if lifecycle.get("status") != "ok":
        failures.append("lifecycle_status_not_ok")
    if inventory.get("status") != "ok":
        failures.append("inventory_status_not_ok")

    discovery_by_alpha = {str(item.get("alpha_id") or ""): item for item in list(discovery.get("items") or [])}
    if str(discovery_by_alpha.get("alpha.trend.next", {}).get("discovery_priority") or "") != "high":
        failures.append("trend_discovery_priority_invalid")

    validation_by_alpha = {str(item.get("alpha_id") or ""): item for item in list(validation.get("items") or [])}
    if str(validation_by_alpha.get("alpha.trend.next", {}).get("validation_status") or "") != "pass":
        failures.append("trend_validation_status_invalid")
    if str(validation_by_alpha.get("alpha.event.fail", {}).get("validation_status") or "") != "fail":
        failures.append("event_validation_status_invalid")

    admission_by_alpha = {str(item.get("alpha_id") or ""): item for item in list(admission.get("items") or [])}
    if str(admission_by_alpha.get("alpha.trend.next", {}).get("alpha_admission_decision") or "") != "admit":
        failures.append("trend_admission_invalid")
    if str(admission_by_alpha.get("alpha.carry.shadow", {}).get("alpha_admission_decision") or "") != "shadow":
        failures.append("carry_admission_invalid")

    lifecycle_by_alpha = {str(item.get("alpha_id") or ""): item for item in list(lifecycle.get("items") or [])}
    if str(lifecycle_by_alpha.get("alpha.carry.shadow", {}).get("lifecycle_stage") or "") != "shadow":
        failures.append("carry_lifecycle_invalid")

    health = inventory.get("alpha_inventory_health") or {}
    if str(health.get("health_status") or "") not in {"healthy", "watch", "fragile"}:
        failures.append("inventory_health_status_invalid")
    if "replacement_pressure" not in health:
        failures.append("inventory_replacement_pressure_missing")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
