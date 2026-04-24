from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Autonomous_alpha_expansion_strategy_generation_intelligence_packet04_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_aae04_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/alpha-next-cycle-learning-input/latest",
            "/system/alpha-next-cycle-policy-bridge/latest",
            "/system/alpha-regime-adaptation-input/latest",
            "/system/alpha-universe-refresh-priorities/latest",
            "/system/alpha-expansion-learning-effectiveness/latest",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.autonomous_alpha_expansion_strategy_generation_intelligence_service import (
        AutonomousAlphaExpansionStrategyGenerationIntelligenceService,
    )

    service = AutonomousAlphaExpansionStrategyGenerationIntelligenceService()

    service.alpha_runtime_governance_feedback_latest = lambda limit=20: {
        "status": "ok",
        "items": [
            {"alpha_family": "trend", "alpha_id": "alpha.trend.1", "runtime_feedback_status": "healthy"},
            {"alpha_family": "carry", "alpha_id": "alpha.carry.1", "runtime_feedback_status": "watch"},
            {"alpha_family": "event", "alpha_id": "alpha.event.1", "runtime_feedback_status": "intervention_required"},
        ],
    }
    service.alpha_runtime_rollback_response_latest = lambda limit=20: {
        "status": "ok",
        "items": [
            {"alpha_family": "trend", "alpha_id": "alpha.trend.1", "runtime_rollback_response": "hold"},
            {"alpha_family": "carry", "alpha_id": "alpha.carry.1", "runtime_rollback_response": "reduce"},
            {"alpha_family": "event", "alpha_id": "alpha.event.1", "runtime_rollback_response": "rollback"},
        ],
    }
    service.alpha_runtime_champion_challenger_latest = lambda limit=20: {
        "status": "ok",
        "items": [
            {"alpha_family": "trend", "runtime_competition_role": "current_champion", "runtime_competition_action": "keep_runtime_champion_live"},
            {"alpha_family": "carry", "runtime_competition_role": "observer", "runtime_competition_action": "hold_current_runtime_posture"},
            {"alpha_family": "event", "runtime_competition_role": "challenger_winner", "runtime_competition_action": "switch_runtime_to_challenger"},
        ],
    }
    service.system_learning.policy_updates_latest = lambda limit=20: {
        "status": "ok",
        "items": [
            {
                "alpha_family": "trend",
                "learning_action": "reinforce",
                "selection_score_adjustment": 0.08,
                "capital_multiplier_adjustment": 1.1,
                "review_pressure": "increase",
                "runtime_caution": "normal",
                "policy_update_reason_codes": ["positive_feedback_supported_across_layers"],
            },
            {
                "alpha_family": "carry",
                "learning_action": "rebalance",
                "selection_score_adjustment": -0.03,
                "capital_multiplier_adjustment": 0.95,
                "review_pressure": "rebalance",
                "runtime_caution": "elevated",
                "policy_update_reason_codes": ["mixed_feedback_requires_rebalance"],
            },
            {
                "alpha_family": "event",
                "learning_action": "caution",
                "selection_score_adjustment": -0.12,
                "capital_multiplier_adjustment": 0.75,
                "review_pressure": "decrease",
                "runtime_caution": "high",
                "policy_update_reason_codes": ["negative_feedback_dominant"],
            },
        ],
    }
    service.strategy_evolution.strategy_gating_decision_latest = lambda limit=20: {
        "status": "ok",
        "current_regime": "transition",
        "regime_confidence": 0.72,
        "system_regime_action": "observe_regime_shift_and_prepare_gating",
        "items": [
            {"alpha_family": "trend", "family_regime_state": "risk_on", "strategy_gating_decision": "allow"},
            {"alpha_family": "carry", "family_regime_state": "transition", "strategy_gating_decision": "shadow"},
            {"alpha_family": "event", "family_regime_state": "risk_off", "strategy_gating_decision": "gate"},
        ],
    }
    service.alpha_discovery_candidates_latest = lambda limit=20: {
        "status": "ok",
        "items": [
            {"alpha_family": "trend", "discovery_priority": "high"},
            {"alpha_family": "carry", "discovery_priority": "medium"},
            {"alpha_family": "event", "discovery_priority": "low"},
        ],
    }
    service.alpha_generation_agenda_latest = lambda limit=20: {
        "status": "ok",
        "items": [
            {"alpha_family": "trend", "generation_action": "hold_generation_capacity"},
            {"alpha_family": "carry", "generation_action": "expand_generation_now"},
            {"alpha_family": "event", "generation_action": "expand_generation_now"},
        ],
    }

    learning_input = service.alpha_next_cycle_learning_input_latest(limit=10)
    policy_bridge = service.alpha_next_cycle_policy_bridge_latest(limit=10)
    regime_input = service.alpha_regime_adaptation_input_latest(limit=10)
    universe = service.alpha_universe_refresh_priorities_latest(limit=10)
    effectiveness = service.alpha_expansion_learning_effectiveness_latest(limit=10)

    learning_by_family = {str(item.get("alpha_family") or ""): item for item in list(learning_input.get("items") or [])}
    policy_by_family = {str(item.get("alpha_family") or ""): item for item in list(policy_bridge.get("items") or [])}
    regime_by_family = {str(item.get("alpha_family") or ""): item for item in list(regime_input.get("items") or [])}
    universe_by_family = {str(item.get("alpha_family") or ""): item for item in list(universe.get("items") or [])}

    if str(learning_by_family.get("trend", {}).get("next_cycle_learning_input") or "") != "reinforce":
        failures.append("trend_learning_input_invalid")
    if str(learning_by_family.get("carry", {}).get("next_cycle_learning_input") or "") != "rebalance":
        failures.append("carry_learning_input_invalid")
    if str(learning_by_family.get("event", {}).get("next_cycle_learning_input") or "") != "caution":
        failures.append("event_learning_input_invalid")

    if str(policy_by_family.get("trend", {}).get("policy_bridge_state") or "") != "expand":
        failures.append("trend_policy_bridge_invalid")
    if str(regime_by_family.get("event", {}).get("regime_adaptation_input") or "") != "prune":
        failures.append("event_regime_input_invalid")
    if str(universe_by_family.get("trend", {}).get("universe_refresh_priority") or "") != "expand":
        failures.append("trend_universe_priority_invalid")
    if str(universe_by_family.get("carry", {}).get("universe_refresh_priority") or "") != "replace":
        failures.append("carry_universe_priority_invalid")

    eff = effectiveness.get("alpha_expansion_learning_effectiveness") or {}
    if str(eff.get("effectiveness_status") or "") not in {"closed_loop_ready", "watch", "fragile"}:
        failures.append("learning_effectiveness_status_invalid")
    if "system_alpha_expansion_learning_action" not in eff:
        failures.append("learning_effectiveness_action_missing")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
