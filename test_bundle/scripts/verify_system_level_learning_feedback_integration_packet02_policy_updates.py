from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "System_level_learning_feedback_integration_packet02_policy_updates_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_sllfi02_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/learning-policy-updates/latest",
            "selection_score_adjustment",
            "capital_multiplier_adjustment",
            "system_policy_action",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.system_level_learning_feedback_integration_service import (
        SystemLevelLearningFeedbackIntegrationService,
    )

    service = SystemLevelLearningFeedbackIntegrationService()
    service.latest = lambda limit=20: {
        "status": "ok",
        "run_id": "run-sllfi-next",
        "cycle_id": "cycle-sllfi-next",
        "mode": "shadow",
        "items": [
            {
                "alpha_family": "mean_reversion",
                "learning_action": "reinforce",
                "learning_reason_codes": ["beneficial_realized_feedback_present", "positive_governed_transition_present"],
            },
            {
                "alpha_family": "event",
                "learning_action": "caution",
                "learning_reason_codes": ["negative_governed_transition_present"],
            },
            {
                "alpha_family": "momentum",
                "learning_action": "rebalance",
                "learning_reason_codes": ["mixed_feedback_requires_rebalance"],
            },
        ],
        "cross_layer_coherence": {
            "run_id_coherent": True,
            "cycle_id_coherent": True,
            "mode_coherent": True,
            "coherent": True,
        },
        "source_packets": {
            "portfolio": "PI-05",
            "selection": "ASI-05",
            "research_promotion_persisted_state": "RPI-06",
        },
        "feedback_summary": {
            "family_count": 3,
            "reinforce_families": 1,
            "caution_families": 1,
            "rebalance_families": 1,
            "observe_families": 0,
            "system_learning_action": "rebalance_mixed_feedback",
        },
        "control_context": {},
        "as_of": "2026-04-02T00:00:00+00:00",
    }
    payload = service.policy_updates_latest(limit=20)
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")

    coherence = payload.get("cross_layer_coherence") or {}
    if not bool(coherence.get("coherent")):
        failures.append("cross_layer_not_coherent")

    by_family = {str(item.get("alpha_family") or ""): item for item in list(payload.get("items") or [])}
    mean_reversion = by_family.get("mean_reversion", {})
    event_family = by_family.get("event", {})

    if float(mean_reversion.get("selection_score_adjustment", 0.0) or 0.0) <= 0.0:
        failures.append("mean_reversion_adjustment_should_be_positive")
    if float(mean_reversion.get("capital_multiplier_adjustment", 0.0) or 0.0) <= 1.0:
        failures.append("mean_reversion_capital_multiplier_should_expand")
    if str(mean_reversion.get("review_pressure") or "") != "increase":
        failures.append("mean_reversion_review_pressure_invalid")

    if float(event_family.get("selection_score_adjustment", 0.0) or 0.0) >= 0.0:
        failures.append("event_adjustment_should_be_negative")
    if float(event_family.get("capital_multiplier_adjustment", 1.0) or 1.0) >= 1.0:
        failures.append("event_capital_multiplier_should_contract")
    if str(event_family.get("runtime_caution") or "") != "high":
        failures.append("event_runtime_caution_invalid")

    summary = payload.get("policy_update_summary") or {}
    if int(summary.get("reinforce_updates", 0) or 0) < 1:
        failures.append("reinforce_updates_invalid")
    if int(summary.get("caution_updates", 0) or 0) < 1:
        failures.append("caution_updates_invalid")
    if str(summary.get("system_policy_action") or "") not in {
        "hold_current_policy",
        "tighten_policy_for_negative_families",
        "rebalance_policy_mixed_families",
        "increase_policy_support_for_positive_families",
    }:
        failures.append("system_policy_action_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
