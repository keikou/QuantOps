from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "System_level_learning_feedback_integration_packet04_resolved_overrides_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-sllfi04-", dir=str(REPO_ROOT / "runtime")))

os.environ["AHB_RUNTIME_DIR"] = str(TEST_RUNTIME_DIR)

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_sllfi04_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/learning-resolved-overrides/latest",
            "override_state",
            "selection_override",
            "system_override_action",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.system_level_learning_feedback_integration_service import (
        SystemLevelLearningFeedbackIntegrationService,
    )

    service = SystemLevelLearningFeedbackIntegrationService()
    service.persisted_policy_state_latest = lambda limit=20: {
        "status": "ok",
        "run_id": "run-sllfi-next",
        "cycle_id": "cycle-sllfi-next",
        "mode": "shadow",
        "items": [
            {
                "alpha_family": "mean_reversion",
                "learning_action": "reinforce",
                "applied_selection_score_adjustment": 0.08,
                "applied_capital_multiplier": 1.1,
                "applied_review_pressure": "increase",
                "applied_runtime_caution": "normal",
            },
            {
                "alpha_family": "event",
                "learning_action": "caution",
                "applied_selection_score_adjustment": -0.12,
                "applied_capital_multiplier": 0.75,
                "applied_review_pressure": "decrease",
                "applied_runtime_caution": "high",
            },
            {
                "alpha_family": "momentum",
                "learning_action": "rebalance",
                "applied_selection_score_adjustment": -0.03,
                "applied_capital_multiplier": 0.95,
                "applied_review_pressure": "rebalance",
                "applied_runtime_caution": "elevated",
            },
        ],
        "cross_layer_coherence": {"coherent": True},
        "source_packets": {},
        "feedback_summary": {},
        "policy_update_summary": {},
        "persisted_policy_state_summary": {"persisted_states": 3},
        "control_context": {},
        "as_of": "2026-04-02T00:00:00+00:00",
    }

    payload = service.resolved_overrides_latest(limit=20)
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")

    by_family = {str(item.get("alpha_family") or ""): item for item in list(payload.get("items") or [])}
    mean_reversion = by_family.get("mean_reversion", {})
    event_family = by_family.get("event", {})
    momentum = by_family.get("momentum", {})

    if str(mean_reversion.get("override_state") or "") != "expand":
        failures.append("mean_reversion_override_state_invalid")
    if str((mean_reversion.get("capital_override") or {}).get("capital_bias") or "") != "expand":
        failures.append("mean_reversion_capital_bias_invalid")
    if str(event_family.get("override_state") or "") != "constrain":
        failures.append("event_override_state_invalid")
    if str((event_family.get("runtime_override") or {}).get("runtime_caution") or "") != "high":
        failures.append("event_runtime_override_invalid")
    if str(momentum.get("override_state") or "") != "mixed":
        failures.append("momentum_override_state_invalid")

    summary = payload.get("resolved_override_summary") or {}
    if int(summary.get("expand_overrides", 0) or 0) < 1:
        failures.append("expand_override_count_invalid")
    if int(summary.get("constrain_overrides", 0) or 0) < 1:
        failures.append("constrain_override_count_invalid")
    if str(summary.get("system_override_action") or "") not in {
        "hold_overrides",
        "apply_constraining_overrides",
        "apply_mixed_overrides",
        "apply_expansion_overrides",
    }:
        failures.append("system_override_action_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
