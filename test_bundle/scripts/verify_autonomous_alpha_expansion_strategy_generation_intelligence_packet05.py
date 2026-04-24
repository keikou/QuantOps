from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Autonomous_alpha_expansion_strategy_generation_intelligence_packet05_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_aae05_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/alpha-promotion-bridge/latest",
            "/system/alpha-family-capital-intent/latest",
            "/system/alpha-portfolio-intake-queue/latest",
            "/system/alpha-governed-universe-state/latest",
            "/system/alpha-strategy-factory-readiness/latest",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.autonomous_alpha_expansion_strategy_generation_intelligence_service import (
        AutonomousAlphaExpansionStrategyGenerationIntelligenceService,
    )

    service = AutonomousAlphaExpansionStrategyGenerationIntelligenceService()

    service.alpha_universe_refresh_priorities_latest = lambda limit=20: {
        "status": "ok",
        "items": [
            {"alpha_family": "trend", "universe_refresh_priority": "expand", "universe_refresh_action": "expand_family_with_validated_candidates"},
            {"alpha_family": "carry", "universe_refresh_priority": "hold", "universe_refresh_action": "hold_family_universe"},
            {"alpha_family": "event", "universe_refresh_priority": "prune", "universe_refresh_action": "prune_or_replace_fragile_family_capacity"},
        ],
    }
    service.research_promotion.promotion_agenda_latest = lambda limit=20: {
        "status": "ok",
        "items": [
            {"alpha_id": "alpha.trend.1", "alpha_family": "trend", "selection_score": 0.91, "promotion_action": "promote", "review_priority": "immediate"},
            {"alpha_id": "alpha.carry.1", "alpha_family": "carry", "selection_score": 0.74, "promotion_action": "advance", "review_priority": "high"},
            {"alpha_id": "alpha.event.1", "alpha_family": "event", "selection_score": 0.28, "promotion_action": "retire", "review_priority": "low"},
        ],
    }
    service.alpha_next_cycle_policy_bridge_latest = lambda limit=20: {
        "status": "ok",
        "items": [
            {"alpha_family": "trend", "policy_bridge_state": "expand", "capital_multiplier_adjustment": 1.12},
            {"alpha_family": "carry", "policy_bridge_state": "hold", "capital_multiplier_adjustment": 1.0},
            {"alpha_family": "event", "policy_bridge_state": "constrain", "capital_multiplier_adjustment": 0.78},
        ],
    }
    service.policy_optimization.outcome_effectiveness_latest = lambda limit=20: {
        "status": "ok",
        "items": [
            {"alpha_family": "trend", "realized_effect": "beneficial"},
            {"alpha_family": "carry", "realized_effect": "neutral"},
            {"alpha_family": "event", "realized_effect": "adverse"},
        ],
    }
    service.alpha_admission_decision_latest = lambda limit=20: {
        "status": "ok",
        "items": [
            {"alpha_id": "alpha.trend.1", "alpha_family": "trend", "rank_score": 0.93, "alpha_admission_decision": "admit", "current_lifecycle_state": "candidate"},
            {"alpha_id": "alpha.carry.1", "alpha_family": "carry", "rank_score": 0.71, "alpha_admission_decision": "shadow", "current_lifecycle_state": "candidate"},
            {"alpha_id": "alpha.event.1", "alpha_family": "event", "rank_score": 0.22, "alpha_admission_decision": "reject", "current_lifecycle_state": "candidate"},
        ],
    }
    service.research_promotion.persisted_governed_state_transitions_latest = lambda limit=20: {
        "status": "ok",
        "items": [
            {"alpha_id": "alpha.trend.1", "new_governed_state": "promoted", "transition_id": "t1", "authority_surface": "research_promotion_intelligence_rpi06"},
            {"alpha_id": "alpha.carry.1", "new_governed_state": "shadow", "transition_id": "t2", "authority_surface": "research_promotion_intelligence_rpi06"},
            {"alpha_id": "alpha.event.1", "new_governed_state": "retired", "transition_id": "t3", "authority_surface": "research_promotion_intelligence_rpi06"},
        ],
    }

    promotion = service.alpha_promotion_bridge_latest(limit=10)
    capital = service.alpha_family_capital_intent_latest(limit=10)
    intake = service.alpha_portfolio_intake_queue_latest(limit=10)
    governed = service.alpha_governed_universe_state_latest(limit=10)
    readiness = service.alpha_strategy_factory_readiness_latest(limit=10)

    promotion_by_alpha = {str(item.get("alpha_id") or ""): item for item in list(promotion.get("items") or [])}
    capital_by_family = {str(item.get("alpha_family") or ""): item for item in list(capital.get("items") or [])}
    intake_by_alpha = {str(item.get("alpha_id") or ""): item for item in list(intake.get("items") or [])}
    governed_by_alpha = {str(item.get("alpha_id") or ""): item for item in list(governed.get("items") or [])}

    if str(promotion_by_alpha.get("alpha.trend.1", {}).get("promotion_bridge_status") or "") != "accelerate":
        failures.append("trend_promotion_bridge_invalid")
    if str(capital_by_family.get("trend", {}).get("capital_intent") or "") != "expand":
        failures.append("trend_capital_intent_invalid")
    if str(capital_by_family.get("event", {}).get("capital_intent") or "") != "constrain":
        failures.append("event_capital_intent_invalid")
    if str(intake_by_alpha.get("alpha.trend.1", {}).get("portfolio_intake_status") or "") != "queue_now":
        failures.append("trend_portfolio_intake_invalid")
    if str(governed_by_alpha.get("alpha.event.1", {}).get("governed_universe_state") or "") != "prune":
        failures.append("event_governed_state_invalid")

    readiness_payload = readiness.get("alpha_strategy_factory_readiness") or {}
    if str(readiness_payload.get("readiness_status") or "") not in {"ready", "watch", "fragile"}:
        failures.append("strategy_factory_readiness_status_invalid")
    if "system_alpha_strategy_factory_action" not in readiness_payload:
        failures.append("strategy_factory_action_missing")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
