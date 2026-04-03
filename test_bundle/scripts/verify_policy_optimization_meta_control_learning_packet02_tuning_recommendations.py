from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Policy_optimization_meta_control_learning_packet02_tuning_recommendations_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-po02-", dir=str(REPO_ROOT / "runtime")))

os.environ["AHB_RUNTIME_DIR"] = str(TEST_RUNTIME_DIR)

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_po02_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/policy-tuning/latest",
            "tuning_action",
            "threshold_adjustment",
            "weight_adjustment",
            "system_tuning_action",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.policy_optimization_meta_control_learning_service import (
        PolicyOptimizationMetaControlLearningService,
    )

    service = PolicyOptimizationMetaControlLearningService()
    service.latest = lambda limit=20: {
        "status": "ok",
        "run_id": "run-po02",
        "cycle_id": "cycle-po02",
        "mode": "shadow",
        "consumed_run_id": "run-po02:next",
        "consumed_cycle_id": "cycle-po02:next",
        "items": [
            {"alpha_family": "trend", "effect_classification": "beneficial", "observed_policy_cycles": 2},
            {"alpha_family": "carry", "effect_classification": "neutral", "observed_policy_cycles": 1},
            {"alpha_family": "event", "effect_classification": "adverse", "observed_policy_cycles": 3},
        ],
        "cross_layer_coherence": {"coherent": True},
        "source_packets": {},
        "policy_effectiveness_summary": {"family_count": 3},
        "as_of": "2026-04-03T00:00:00+00:00",
    }

    payload = service.tuning_recommendations_latest(limit=20)
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")

    by_family = {str(item.get("alpha_family") or ""): item for item in list(payload.get("items") or [])}
    trend = by_family.get("trend", {})
    carry = by_family.get("carry", {})
    event = by_family.get("event", {})

    if str(trend.get("tuning_action") or "") != "reinforce":
        failures.append("trend_tuning_action_invalid")
    if float(((trend.get("tuning_adjustments") or {}).get("weight_adjustment", 0.0) or 0.0)) <= 0.0:
        failures.append("trend_weight_adjustment_invalid")

    if str(carry.get("tuning_action") or "") != "hold":
        failures.append("carry_tuning_action_invalid")
    if str(((carry.get("tuning_adjustments") or {}).get("escalation_rule") or "")) != "collect_more_evidence":
        failures.append("carry_escalation_rule_invalid")

    if str(event.get("tuning_action") or "") != "retune":
        failures.append("event_tuning_action_invalid")
    if float(((event.get("tuning_adjustments") or {}).get("threshold_adjustment", 0.0) or 0.0)) >= 0.0:
        failures.append("event_threshold_adjustment_invalid")

    summary = payload.get("tuning_summary") or {}
    if int(summary.get("family_count", 0) or 0) != 3:
        failures.append("summary_family_count_invalid")
    if int(summary.get("retune_families", 0) or 0) != 1:
        failures.append("summary_retune_count_invalid")
    if str(summary.get("system_tuning_action") or "") != "retune_adverse_policy_families":
        failures.append("summary_system_tuning_action_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
