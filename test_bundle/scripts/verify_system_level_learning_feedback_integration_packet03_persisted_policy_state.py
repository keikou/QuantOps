from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "System_level_learning_feedback_integration_packet03_persisted_policy_state_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-sllfi03-", dir=str(REPO_ROOT / "runtime")))

os.environ["AHB_RUNTIME_DIR"] = str(TEST_RUNTIME_DIR)

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_sllfi03_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/learning-policy-state/latest",
            "policy_state_id",
            "applied_selection_score_adjustment",
            "system_policy_state_action",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.app.container import CONTAINER
    from ai_hedge_bot.services.system_level_learning_feedback_integration_service import (
        SystemLevelLearningFeedbackIntegrationService,
    )

    try:
        CONTAINER.runtime_store.execute("DELETE FROM audit_logs")
    except Exception:
        pass

    service = SystemLevelLearningFeedbackIntegrationService()
    service.policy_updates_latest = lambda limit=20: {
        "status": "ok",
        "run_id": "run-sllfi-next",
        "cycle_id": "cycle-sllfi-next",
        "mode": "shadow",
        "items": [
            {
                "alpha_family": "mean_reversion",
                "learning_action": "reinforce",
                "selection_score_adjustment": 0.08,
                "capital_multiplier_adjustment": 1.1,
                "review_pressure": "increase",
                "runtime_caution": "normal",
            },
            {
                "alpha_family": "event",
                "learning_action": "caution",
                "selection_score_adjustment": -0.12,
                "capital_multiplier_adjustment": 0.75,
                "review_pressure": "decrease",
                "runtime_caution": "high",
            },
        ],
        "cross_layer_coherence": {"coherent": True},
        "source_packets": {
            "portfolio": "PI-05",
            "selection": "ASI-05",
            "research_promotion_persisted_state": "RPI-06",
        },
        "feedback_summary": {},
        "policy_update_summary": {
            "family_count": 2,
            "reinforce_updates": 1,
            "caution_updates": 1,
            "rebalance_updates": 0,
            "observe_updates": 0,
            "system_policy_action": "tighten_policy_for_negative_families",
        },
        "control_context": {},
        "as_of": "2026-04-02T00:00:00+00:00",
    }

    payload = service.persisted_policy_state_latest(limit=20)
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")

    items = list(payload.get("items") or [])
    if len(items) != 2:
        failures.append("persisted_item_count_invalid")

    by_family = {str(item.get("alpha_family") or ""): item for item in items}
    if not by_family.get("mean_reversion", {}).get("policy_state_id"):
        failures.append("mean_reversion_policy_state_missing")
    if float(by_family.get("event", {}).get("applied_capital_multiplier", 1.0) or 1.0) >= 1.0:
        failures.append("event_applied_capital_multiplier_invalid")
    if str(by_family.get("event", {}).get("policy_source_packet") or "") != "SLLFI-02":
        failures.append("policy_source_packet_invalid")

    summary = payload.get("persisted_policy_state_summary") or {}
    if int(summary.get("persisted_states", 0) or 0) != 2:
        failures.append("persisted_state_count_invalid")
    if str(summary.get("system_policy_state_action") or "") != "persist_next_cycle_learning_policy":
        failures.append("system_policy_state_action_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
