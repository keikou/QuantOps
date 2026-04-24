from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Autonomous_alpha_expansion_strategy_generation_intelligence_packet02_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_aae02_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/alpha-generation-agenda/latest",
            "/system/alpha-experiment-docket/latest",
            "/system/alpha-replacement-decision/latest",
            "/system/alpha-replacement-state/latest",
            "/system/alpha-expansion-effectiveness/latest",
            "system_alpha_expansion_action",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.autonomous_alpha_expansion_strategy_generation_intelligence_service import (
        AutonomousAlphaExpansionStrategyGenerationIntelligenceService,
    )

    service = AutonomousAlphaExpansionStrategyGenerationIntelligenceService()

    service.alpha_discovery_candidates_latest = lambda limit=20: {
        "status": "ok",
        "items": [
            {"alpha_id": "alpha.trend.next", "alpha_family": "trend", "candidate_state": "candidate", "family_regime_state": "risk_on", "discovery_priority": "high", "feature_dependencies": ["momentum_4"]},
            {"alpha_id": "alpha.carry.shadow", "alpha_family": "carry", "candidate_state": "validated", "family_regime_state": "balanced", "discovery_priority": "medium", "feature_dependencies": ["funding_rate"]},
            {"alpha_id": "alpha.event.fail", "alpha_family": "event", "candidate_state": "candidate", "family_regime_state": "risk_off", "discovery_priority": "low", "feature_dependencies": ["volume_spike"]},
        ],
    }
    service.alpha_inventory_health_latest = lambda limit=20: {
        "status": "ok",
        "alpha_inventory_health": {"replacement_pressure": "high"},
    }
    service._regime_context = lambda limit=20: {
        "current_regime": "transition",
        "regime_confidence": 0.66,
        "family_regime_state": {"trend": "risk_on", "carry": "balanced", "event": "risk_off"},
        "system_regime_action": "observe_regime_shift_and_prepare_gating",
    }
    service._latest_experiment_rows = lambda limit=200: [
        {"alpha_id": "alpha.trend.next", "experiment_id": "exp-trend", "status": "generated"},
        {"alpha_id": "alpha.carry.shadow", "experiment_id": "exp-carry", "status": "tested"},
    ]
    service._latest_validation_rows = lambda limit=200: [
        {"experiment_id": "exp-trend", "summary_score": 0.87, "passed": True},
        {"experiment_id": "exp-carry", "summary_score": 0.74, "passed": True},
    ]
    service.alpha_admission_decision_latest = lambda limit=20: {
        "status": "ok",
        "items": [
            {"alpha_id": "alpha.trend.next", "alpha_family": "trend", "alpha_admission_decision": "admit", "rank_score": 0.86},
            {"alpha_id": "alpha.carry.shadow", "alpha_family": "carry", "alpha_admission_decision": "shadow", "rank_score": 0.73},
            {"alpha_id": "alpha.event.fail", "alpha_family": "event", "alpha_admission_decision": "reject", "rank_score": 0.42},
        ],
    }
    service.alpha_lifecycle_state_latest = lambda limit=20: {
        "status": "ok",
        "items": [
            {"alpha_id": "alpha.trend.next", "lifecycle_stage": "validation"},
            {"alpha_id": "alpha.carry.shadow", "lifecycle_stage": "shadow"},
            {"alpha_id": "alpha.event.fail", "lifecycle_stage": "research"},
        ],
    }
    service._latest_promotion_rows = lambda limit=200: [
        {"alpha_id": "alpha.trend.next", "promotion_id": "promo-trend", "notes": "promoted by rank"},
    ]
    service._latest_demotion_rows = lambda limit=200: [
        {"alpha_id": "alpha.event.fail", "demotion_id": "demo-event", "notes": "returned to research"},
    ]

    agenda = service.alpha_generation_agenda_latest(limit=10)
    docket = service.alpha_experiment_docket_latest(limit=10)
    replacement = service.alpha_replacement_decision_latest(limit=10)
    state = service.alpha_replacement_state_latest(limit=10)
    effectiveness = service.alpha_expansion_effectiveness_latest(limit=10)

    agenda_by_alpha = {str(item.get("alpha_id") or ""): item for item in list(agenda.get("items") or [])}
    docket_by_alpha = {str(item.get("alpha_id") or ""): item for item in list(docket.get("items") or [])}
    replacement_by_alpha = {str(item.get("alpha_id") or ""): item for item in list(replacement.get("items") or [])}
    state_by_alpha = {str(item.get("alpha_id") or ""): item for item in list(state.get("items") or [])}

    if str(agenda_by_alpha.get("alpha.trend.next", {}).get("generation_priority") or "") != "expand_now":
        failures.append("trend_generation_priority_invalid")
    if str(docket_by_alpha.get("alpha.trend.next", {}).get("docket_state") or "") != "ready":
        failures.append("trend_docket_state_invalid")
    if str(replacement_by_alpha.get("alpha.trend.next", {}).get("alpha_replacement_decision") or "") != "replace":
        failures.append("trend_replacement_decision_invalid")
    if str(replacement_by_alpha.get("alpha.carry.shadow", {}).get("alpha_replacement_decision") or "") != "shadow":
        failures.append("carry_replacement_decision_invalid")
    if str(state_by_alpha.get("alpha.trend.next", {}).get("replacement_state") or "") != "active":
        failures.append("trend_replacement_state_invalid")

    eff = effectiveness.get("alpha_expansion_effectiveness") or {}
    if str(eff.get("expansion_status") or "") not in {"effective", "watch", "insufficient"}:
        failures.append("expansion_status_invalid")
    if "system_alpha_expansion_action" not in eff:
        failures.append("system_alpha_expansion_action_missing")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
