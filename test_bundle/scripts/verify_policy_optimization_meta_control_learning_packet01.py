from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Policy_optimization_meta_control_learning_packet01_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-po01-", dir=str(REPO_ROOT / "runtime")))

os.environ["AHB_RUNTIME_DIR"] = str(TEST_RUNTIME_DIR)

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_po01_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/policy-effectiveness/latest",
            "effect_classification",
            "policy_paths.selection",
            "observed_policy_cycles",
            "system_policy_optimization_action",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.policy_optimization_meta_control_learning_service import (
        PolicyOptimizationMetaControlLearningService,
    )

    service = PolicyOptimizationMetaControlLearningService()
    service.system_learning.applied_override_consumption_latest = lambda limit=20: {
        "status": "ok",
        "run_id": "run-po01",
        "cycle_id": "cycle-po01",
        "mode": "shadow",
        "consumed_run_id": "run-po01:next",
        "consumed_cycle_id": "cycle-po01:next",
        "items": [
            {
                "alpha_family": "trend",
                "consumed_run_id": "run-po01:next",
                "consumed_cycle_id": "cycle-po01:next",
                "consumed_effect": "expansion_applied",
                "override_state": "expand",
                "selection_consumption": {
                    "applied_score_adjustment": 0.08,
                    "applied_selection_bias": "favor",
                },
                "capital_consumption": {
                    "applied_capital_multiplier": 1.1,
                    "applied_capital_bias": "expand",
                },
                "review_consumption": {
                    "applied_review_pressure": "increase",
                },
                "runtime_consumption": {
                    "applied_runtime_caution": "normal",
                },
            },
            {
                "alpha_family": "event",
                "consumed_run_id": "run-po01:next",
                "consumed_cycle_id": "cycle-po01:next",
                "consumed_effect": "constraint_applied",
                "override_state": "constrain",
                "selection_consumption": {
                    "applied_score_adjustment": -0.12,
                    "applied_selection_bias": "penalize",
                },
                "capital_consumption": {
                    "applied_capital_multiplier": 0.75,
                    "applied_capital_bias": "constrain",
                },
                "review_consumption": {
                    "applied_review_pressure": "decrease",
                },
                "runtime_consumption": {
                    "applied_runtime_caution": "high",
                },
            },
        ],
        "cross_layer_coherence": {"coherent": True},
        "as_of": "2026-04-03T00:00:00+00:00",
    }
    service.system_learning.latest = lambda limit=20: {
        "status": "ok",
        "items": [
            {
                "alpha_family": "trend",
                "portfolio_feedback": {
                    "beneficial_actions": 2,
                    "neutral_actions": 0,
                    "adverse_actions": 0,
                    "drag_change_usd_total": -4.0,
                    "resolved_weight_change_total": 0.2,
                    "concentration_change_total": -0.05,
                },
                "governed_transition_feedback": {
                    "promoted_states": 1,
                    "shadow_states": 0,
                    "retired_states": 0,
                    "rejected_states": 0,
                    "candidate_states": 0,
                },
            },
            {
                "alpha_family": "event",
                "portfolio_feedback": {
                    "beneficial_actions": 0,
                    "neutral_actions": 0,
                    "adverse_actions": 2,
                    "drag_change_usd_total": 5.0,
                    "resolved_weight_change_total": -0.2,
                    "concentration_change_total": 0.04,
                },
                "governed_transition_feedback": {
                    "promoted_states": 0,
                    "shadow_states": 0,
                    "retired_states": 1,
                    "rejected_states": 0,
                    "candidate_states": 0,
                },
            },
        ],
    }

    service.store.append(
        "audit_logs",
        [
            {
                "audit_id": "state-trend-1",
                "created_at": "2026-04-02T00:00:00+00:00",
                "category": "system_learning_policy_state",
                "event_type": "persist_learning_policy_state",
                "run_id": "run-old",
                "payload_json": json.dumps({"applied_learning_action": "reinforce"}),
                "actor": "trend",
            },
            {
                "audit_id": "state-trend-2",
                "created_at": "2026-04-03T00:00:00+00:00",
                "category": "system_learning_policy_state",
                "event_type": "persist_learning_policy_state",
                "run_id": "run-po01",
                "payload_json": json.dumps({"applied_learning_action": "reinforce"}),
                "actor": "trend",
            },
            {
                "audit_id": "state-event-1",
                "created_at": "2026-04-03T00:00:00+00:00",
                "category": "system_learning_policy_state",
                "event_type": "persist_learning_policy_state",
                "run_id": "run-po01",
                "payload_json": json.dumps({"applied_learning_action": "caution"}),
                "actor": "event",
            },
        ],
    )

    payload = service.latest(limit=20)
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")

    by_family = {str(item.get("alpha_family") or ""): item for item in list(payload.get("items") or [])}
    trend = by_family.get("trend", {})
    event = by_family.get("event", {})

    if str(trend.get("effect_classification") or "") != "beneficial":
        failures.append("trend_effect_classification_invalid")
    if int(trend.get("observed_policy_cycles", 0) or 0) < 2:
        failures.append("trend_observed_policy_cycles_invalid")
    if str(((trend.get("policy_paths") or {}).get("selection") or {}).get("effect_classification") or "") != "beneficial":
        failures.append("trend_selection_path_invalid")

    if str(event.get("effect_classification") or "") != "adverse":
        failures.append("event_effect_classification_invalid")
    if str(((event.get("policy_paths") or {}).get("runtime") or {}).get("effect_classification") or "") != "adverse":
        failures.append("event_runtime_path_invalid")
    if "policy_effect:adverse" not in list(event.get("attribution_reason_codes") or []):
        failures.append("event_reason_codes_invalid")

    summary = payload.get("policy_effectiveness_summary") or {}
    if int(summary.get("family_count", 0) or 0) != 2:
        failures.append("summary_family_count_invalid")
    if int(summary.get("beneficial_families", 0) or 0) != 1:
        failures.append("summary_beneficial_count_invalid")
    if int(summary.get("adverse_families", 0) or 0) != 1:
        failures.append("summary_adverse_count_invalid")
    if str(summary.get("system_policy_optimization_action") or "") != "retune_adverse_policy_families":
        failures.append("summary_system_action_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
