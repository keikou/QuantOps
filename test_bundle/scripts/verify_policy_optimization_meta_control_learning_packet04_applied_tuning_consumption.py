from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Policy_optimization_meta_control_learning_packet04_applied_tuning_consumption_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-po04-", dir=str(REPO_ROOT / "runtime")))

os.environ["AHB_RUNTIME_DIR"] = str(TEST_RUNTIME_DIR)

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_po04_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/meta-policy-consumption/latest",
            "applied_tuning_consumption",
            "applied_threshold_adjustment",
            "consumed_effect",
            "system_consumption_action",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.policy_optimization_meta_control_learning_service import (
        PolicyOptimizationMetaControlLearningService,
    )

    service = PolicyOptimizationMetaControlLearningService()
    service.persisted_meta_policy_state_latest = lambda limit=20: {
        "status": "ok",
        "run_id": "run-po04",
        "cycle_id": "cycle-po04",
        "mode": "shadow",
        "items": [
            {
                "alpha_family": "trend",
                "meta_policy_state_id": "state-trend",
                "tuning_action": "reinforce",
                "tuning_adjustments": {
                    "threshold_adjustment": 0.05,
                    "weight_adjustment": 0.08,
                    "escalation_rule": "relax",
                },
            },
            {
                "alpha_family": "carry",
                "meta_policy_state_id": "state-carry",
                "tuning_action": "hold",
                "tuning_adjustments": {
                    "threshold_adjustment": 0.0,
                    "weight_adjustment": 0.0,
                    "escalation_rule": "collect_more_evidence",
                },
            },
            {
                "alpha_family": "event",
                "meta_policy_state_id": "state-event",
                "tuning_action": "retune",
                "tuning_adjustments": {
                    "threshold_adjustment": -0.08,
                    "weight_adjustment": -0.12,
                    "escalation_rule": "tighten",
                },
            },
        ],
        "cross_layer_coherence": {"coherent": True},
        "source_packets": {},
        "policy_effectiveness_summary": {"family_count": 3},
        "tuning_summary": {"family_count": 3},
        "persisted_meta_policy_summary": {"family_count": 3},
        "as_of": "2026-04-03T00:00:00+00:00",
    }

    payload = service.applied_tuning_consumption_latest(limit=20)
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")

    by_family = {str(item.get("alpha_family") or ""): item for item in list(payload.get("items") or [])}
    trend = by_family.get("trend", {})
    carry = by_family.get("carry", {})
    event = by_family.get("event", {})

    if str(trend.get("consumed_effect") or "") != "meta_policy_reinforcement_applied":
        failures.append("trend_consumed_effect_invalid")
    if float(((trend.get("applied_tuning_consumption") or {}).get("applied_weight_adjustment", 0.0) or 0.0)) <= 0.0:
        failures.append("trend_weight_consumption_invalid")

    if str(carry.get("consumed_effect") or "") != "meta_policy_hold_applied":
        failures.append("carry_consumed_effect_invalid")
    if str(((carry.get("applied_tuning_consumption") or {}).get("applied_escalation_rule") or "")) != "collect_more_evidence":
        failures.append("carry_rule_invalid")

    if str(event.get("consumed_effect") or "") != "meta_policy_retune_applied":
        failures.append("event_consumed_effect_invalid")
    if float(((event.get("applied_tuning_consumption") or {}).get("applied_threshold_adjustment", 0.0) or 0.0)) >= 0.0:
        failures.append("event_threshold_consumption_invalid")

    summary = payload.get("applied_tuning_consumption_summary") or {}
    if int(summary.get("family_count", 0) or 0) != 3:
        failures.append("summary_family_count_invalid")
    if int(summary.get("retuned_consumptions", 0) or 0) != 1:
        failures.append("summary_retuned_count_invalid")
    if str(summary.get("system_consumption_action") or "") != "apply_retuned_meta_policy":
        failures.append("summary_consumption_action_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
