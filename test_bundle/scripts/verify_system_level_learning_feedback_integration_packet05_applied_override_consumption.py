from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "System_level_learning_feedback_integration_packet05_applied_override_consumption_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-sllfi05-", dir=str(REPO_ROOT / "runtime")))

os.environ["AHB_RUNTIME_DIR"] = str(TEST_RUNTIME_DIR)

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_sllfi05_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/learning-applied-consumption/latest",
            "selection_consumption",
            "consumed_effect",
            "system_consumption_action",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.system_level_learning_feedback_integration_service import (
        SystemLevelLearningFeedbackIntegrationService,
    )

    service = SystemLevelLearningFeedbackIntegrationService()
    service.resolved_overrides_latest = lambda limit=20: {
        "status": "ok",
        "run_id": "run-sllfi-next",
        "cycle_id": "cycle-sllfi-next",
        "mode": "shadow",
        "items": [
            {
                "alpha_family": "mean_reversion",
                "override_state": "expand",
                "selection_override": {"score_adjustment": 0.08, "selection_bias": "favor"},
                "capital_override": {"capital_multiplier": 1.1, "capital_bias": "expand"},
                "review_override": {"review_pressure": "increase"},
                "runtime_override": {"runtime_caution": "normal"},
            },
            {
                "alpha_family": "event",
                "override_state": "constrain",
                "selection_override": {"score_adjustment": -0.12, "selection_bias": "penalize"},
                "capital_override": {"capital_multiplier": 0.75, "capital_bias": "constrain"},
                "review_override": {"review_pressure": "decrease"},
                "runtime_override": {"runtime_caution": "high"},
            },
        ],
        "cross_layer_coherence": {"coherent": True},
        "source_packets": {},
        "feedback_summary": {},
        "policy_update_summary": {},
        "persisted_policy_state_summary": {},
        "resolved_override_summary": {"family_count": 2},
        "control_context": {},
        "as_of": "2026-04-02T00:00:00+00:00",
    }

    payload = service.applied_override_consumption_latest(limit=20)
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")
    if not str(payload.get("consumed_run_id") or "").endswith(":next"):
        failures.append("consumed_run_id_invalid")

    by_family = {str(item.get("alpha_family") or ""): item for item in list(payload.get("items") or [])}
    mean_reversion = by_family.get("mean_reversion", {})
    event_family = by_family.get("event", {})

    if str(mean_reversion.get("consumed_effect") or "") != "expansion_applied":
        failures.append("mean_reversion_consumed_effect_invalid")
    if not bool((mean_reversion.get("selection_consumption") or {}).get("consumed")):
        failures.append("mean_reversion_selection_not_consumed")
    if str(event_family.get("consumed_effect") or "") != "constraint_applied":
        failures.append("event_consumed_effect_invalid")
    if str((event_family.get("runtime_consumption") or {}).get("applied_runtime_caution") or "") != "high":
        failures.append("event_runtime_consumption_invalid")

    summary = payload.get("applied_consumption_summary") or {}
    if int(summary.get("consumed_overrides", 0) or 0) != 2:
        failures.append("consumed_override_count_invalid")
    if str(summary.get("system_consumption_action") or "") not in {
        "apply_neutral_overrides",
        "apply_constrained_next_cycle",
        "apply_mixed_next_cycle",
        "apply_expanded_next_cycle",
    }:
        failures.append("system_consumption_action_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
