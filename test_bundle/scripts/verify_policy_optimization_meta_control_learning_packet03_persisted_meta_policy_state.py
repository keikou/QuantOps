from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Policy_optimization_meta_control_learning_packet03_persisted_meta_policy_state_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-po03-", dir=str(REPO_ROOT / "runtime")))

os.environ["AHB_RUNTIME_DIR"] = str(TEST_RUNTIME_DIR)

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_po03_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/meta-policy-state/latest",
            "meta_policy_state_id",
            "previous_meta_policy_state_id",
            "policy_source_packet",
            "system_meta_policy_action",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.policy_optimization_meta_control_learning_service import (
        PolicyOptimizationMetaControlLearningService,
    )

    service = PolicyOptimizationMetaControlLearningService()
    service.tuning_recommendations_latest = lambda limit=20: {
        "status": "ok",
        "run_id": "run-po03",
        "cycle_id": "cycle-po03",
        "mode": "shadow",
        "consumed_run_id": "run-po03:next",
        "consumed_cycle_id": "cycle-po03:next",
        "items": [
            {
                "alpha_family": "trend",
                "effect_classification": "beneficial",
                "tuning_action": "reinforce",
                "tuning_adjustments": {
                    "threshold_adjustment": 0.05,
                    "weight_adjustment": 0.08,
                    "escalation_rule": "relax",
                },
            },
            {
                "alpha_family": "event",
                "effect_classification": "adverse",
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
        "policy_effectiveness_summary": {"family_count": 2},
        "tuning_summary": {"family_count": 2},
        "as_of": "2026-04-03T00:00:00+00:00",
    }

    service.store.append(
        "audit_logs",
        {
            "audit_id": "prev-trend-state",
            "created_at": "2026-04-02T00:00:00+00:00",
            "category": "meta_policy_state",
            "event_type": "persist_meta_policy_state",
            "run_id": "run-old",
            "payload_json": json.dumps({"alpha_family": "trend", "tuning_action": "hold"}),
            "actor": "trend",
        },
    )

    payload = service.persisted_meta_policy_state_latest(limit=20)
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")

    by_family = {str(item.get("alpha_family") or ""): item for item in list(payload.get("items") or [])}
    trend = by_family.get("trend", {})
    event = by_family.get("event", {})

    if not str(trend.get("meta_policy_state_id") or ""):
        failures.append("trend_state_id_missing")
    if str(trend.get("previous_meta_policy_state_id") or "") != "prev-trend-state":
        failures.append("trend_previous_state_invalid")
    if str(trend.get("policy_source_packet") or "") != "PO-02":
        failures.append("trend_source_packet_invalid")

    if not str(event.get("meta_policy_state_id") or ""):
        failures.append("event_state_id_missing")
    if str(event.get("tuning_action") or "") != "retune":
        failures.append("event_tuning_action_invalid")
    if str(((event.get("tuning_adjustments") or {}).get("escalation_rule") or "")) != "tighten":
        failures.append("event_escalation_rule_invalid")

    summary = payload.get("persisted_meta_policy_summary") or {}
    if int(summary.get("family_count", 0) or 0) != 2:
        failures.append("summary_family_count_invalid")
    if int(summary.get("persisted_states", 0) or 0) != 2:
        failures.append("summary_persisted_states_invalid")
    if str(summary.get("system_meta_policy_action") or "") != "persist_meta_policy_tuning_state":
        failures.append("summary_action_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
