from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Policy_optimization_meta_control_learning_packet05_outcome_effectiveness_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-po05-", dir=str(REPO_ROOT / "runtime")))

os.environ["AHB_RUNTIME_DIR"] = str(TEST_RUNTIME_DIR)

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_po05_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/meta-policy-effectiveness/latest",
            "intended_objective",
            "realized_effect",
            "effectiveness_reason_codes",
            "system_effectiveness_action",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.policy_optimization_meta_control_learning_service import (
        PolicyOptimizationMetaControlLearningService,
    )

    service = PolicyOptimizationMetaControlLearningService()
    service.applied_tuning_consumption_latest = lambda limit=20: {
        "status": "ok",
        "run_id": "run-po05",
        "cycle_id": "cycle-po05",
        "mode": "shadow",
        "consumed_run_id": "run-po05:meta-next",
        "consumed_cycle_id": "cycle-po05:meta-next",
        "items": [
            {
                "alpha_family": "trend",
                "tuning_action": "reinforce",
                "consumed_effect": "meta_policy_reinforcement_applied",
                "tuning_adjustments": {
                    "threshold_adjustment": 0.05,
                    "weight_adjustment": 0.08,
                },
            },
            {
                "alpha_family": "carry",
                "tuning_action": "hold",
                "consumed_effect": "meta_policy_hold_applied",
                "tuning_adjustments": {
                    "threshold_adjustment": 0.0,
                    "weight_adjustment": 0.0,
                },
            },
            {
                "alpha_family": "event",
                "tuning_action": "retune",
                "consumed_effect": "meta_policy_retune_applied",
                "tuning_adjustments": {
                    "threshold_adjustment": -0.08,
                    "weight_adjustment": -0.12,
                },
            },
        ],
        "cross_layer_coherence": {"coherent": True},
        "source_packets": {},
        "policy_effectiveness_summary": {"family_count": 3},
        "tuning_summary": {"family_count": 3},
        "persisted_meta_policy_summary": {"family_count": 3},
        "applied_tuning_consumption_summary": {"family_count": 3},
        "as_of": "2026-04-03T00:00:00+00:00",
    }

    payload = service.outcome_effectiveness_latest(limit=20)
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")

    by_family = {str(item.get("alpha_family") or ""): item for item in list(payload.get("items") or [])}
    trend = by_family.get("trend", {})
    carry = by_family.get("carry", {})
    event = by_family.get("event", {})

    if str(trend.get("realized_effect") or "") != "beneficial":
        failures.append("trend_realized_effect_invalid")
    if str(carry.get("realized_effect") or "") != "neutral":
        failures.append("carry_realized_effect_invalid")
    if str(event.get("realized_effect") or "") != "beneficial":
        failures.append("event_realized_effect_invalid")
    if str(event.get("intended_objective") or "") != "improve_meta_policy_quality":
        failures.append("event_objective_invalid")

    summary = payload.get("outcome_effectiveness_summary") or {}
    if int(summary.get("family_count", 0) or 0) != 3:
        failures.append("summary_family_count_invalid")
    if int(summary.get("beneficial_families", 0) or 0) != 2:
        failures.append("summary_beneficial_count_invalid")
    if int(summary.get("neutral_families", 0) or 0) != 1:
        failures.append("summary_neutral_count_invalid")
    if str(summary.get("system_effectiveness_action") or "") != "reinforce_effective_meta_policy":
        failures.append("summary_system_effectiveness_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
