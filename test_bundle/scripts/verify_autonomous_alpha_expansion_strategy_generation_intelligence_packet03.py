from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Autonomous_alpha_expansion_strategy_generation_intelligence_packet03_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_aae03_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/alpha-runtime-deployment-candidates/latest",
            "/system/alpha-runtime-governance-feedback/latest",
            "/system/alpha-runtime-rollback-response/latest",
            "/system/alpha-runtime-champion-challenger/latest",
            "/system/alpha-runtime-expansion-effectiveness/latest",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.autonomous_alpha_expansion_strategy_generation_intelligence_service import (
        AutonomousAlphaExpansionStrategyGenerationIntelligenceService,
    )

    service = AutonomousAlphaExpansionStrategyGenerationIntelligenceService()

    service.alpha_replacement_decision_latest = lambda limit=20: {
        "status": "ok",
        "items": [
            {"alpha_id": "alpha.trend.next", "alpha_family": "trend", "alpha_replacement_decision": "replace", "rank_score": 0.86},
            {"alpha_id": "alpha.carry.shadow", "alpha_family": "carry", "alpha_replacement_decision": "shadow", "rank_score": 0.74},
            {"alpha_id": "alpha.event.fail", "alpha_family": "event", "alpha_replacement_decision": "drop", "rank_score": 0.41},
        ],
    }
    service.deployment_rollout.candidate_docket_latest = lambda limit=20: {
        "status": "ok",
        "items": [
            {"alpha_family": "trend", "recommended_rollout_stage": "canary", "approval_status": "ready_for_review", "deployment_action": "prepare_canary_rollout", "rollout_priority": "high"},
            {"alpha_family": "carry", "recommended_rollout_stage": "shadow", "approval_status": "pending_evidence", "deployment_action": "keep_in_shadow", "rollout_priority": "normal"},
            {"alpha_family": "event", "recommended_rollout_stage": "shadow", "approval_status": "denied", "deployment_action": "keep_in_shadow", "rollout_priority": "deprioritized"},
        ],
    }
    service._latest_experiment_rows = lambda limit=200: [
        {"alpha_id": "alpha.trend.next", "experiment_id": "exp-trend"},
        {"alpha_id": "alpha.carry.shadow", "experiment_id": "exp-carry"},
        {"alpha_id": "alpha.event.fail", "experiment_id": "exp-event"},
    ]
    service._latest_model_rows = lambda limit=200: [
        {"model_id": "model-trend", "experiment_id": "exp-trend", "state": "approved"},
        {"model_id": "model-carry", "experiment_id": "exp-carry", "state": "shadow"},
        {"model_id": "model-event", "experiment_id": "exp-event", "state": "candidate"},
    ]
    service._latest_live_review_rows = lambda limit=200: [
        {"model_id": "model-trend", "decision": "keep", "flags": []},
        {"model_id": "model-carry", "decision": "reduce_capital", "flags": ["pnl_drift"]},
        {"model_id": "model-event", "decision": "rollback", "flags": ["drawdown_breach"]},
    ]
    service._latest_decay_rows = lambda limit=200: [
        {"model_id": "model-trend", "severity": "stable", "status": "monitor"},
        {"model_id": "model-carry", "severity": "medium", "status": "review_required"},
        {"model_id": "model-event", "severity": "high", "status": "demote_candidate"},
    ]
    service._latest_rollback_rows = lambda limit=200: [
        {"model_id": "model-event", "action": "rollback", "trigger_reason": "live_review_rollback", "selected_model_id": "model-trend"},
    ]
    service._latest_champion_challenger_rows = lambda limit=200: [
        {"champion_model_id": "model-trend", "challenger_model_id": "model-carry", "winner": "champion", "recommended_action": "keep_live", "capital_shift": 0.0},
    ]
    service.bridge.alpha_id_for_model = lambda model_id: {
        "model-trend": "alpha.trend.next",
        "model-carry": "alpha.carry.shadow",
        "model-event": "alpha.event.fail",
    }.get(model_id)

    deployment = service.alpha_runtime_deployment_candidates_latest(limit=10)
    feedback = service.alpha_runtime_governance_feedback_latest(limit=10)
    rollback = service.alpha_runtime_rollback_response_latest(limit=10)
    champion = service.alpha_runtime_champion_challenger_latest(limit=10)
    effectiveness = service.alpha_runtime_expansion_effectiveness_latest(limit=10)

    deployment_by_alpha = {str(item.get("alpha_id") or ""): item for item in list(deployment.get("items") or [])}
    feedback_by_alpha = {str(item.get("alpha_id") or ""): item for item in list(feedback.get("items") or [])}
    rollback_by_alpha = {str(item.get("alpha_id") or ""): item for item in list(rollback.get("items") or [])}
    champion_by_alpha = {str(item.get("alpha_id") or ""): item for item in list(champion.get("items") or [])}

    if str(deployment_by_alpha.get("alpha.trend.next", {}).get("deployment_candidate_status") or "") != "ready":
        failures.append("trend_runtime_deployment_invalid")
    if str(feedback_by_alpha.get("alpha.carry.shadow", {}).get("runtime_feedback_status") or "") != "watch":
        failures.append("carry_runtime_feedback_invalid")
    if str(rollback_by_alpha.get("alpha.event.fail", {}).get("runtime_rollback_response") or "") != "rollback":
        failures.append("event_runtime_rollback_invalid")
    if str(champion_by_alpha.get("alpha.trend.next", {}).get("runtime_competition_role") or "") != "current_champion":
        failures.append("trend_runtime_competition_invalid")

    eff = effectiveness.get("alpha_runtime_expansion_effectiveness") or {}
    if str(eff.get("effectiveness_status") or "") not in {"effective", "watch", "fragile"}:
        failures.append("runtime_effectiveness_status_invalid")
    if "system_alpha_runtime_expansion_action" not in eff:
        failures.append("runtime_expansion_action_missing")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
