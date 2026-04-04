from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Deployment_rollout_intelligence_packet04_applied_rollout_consumption_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-dri04-", dir=str(REPO_ROOT / "runtime")))

os.environ["AHB_RUNTIME_DIR"] = str(TEST_RUNTIME_DIR)

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_dri04_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/deployment-rollout-consumption/latest",
            "applied_rollout_consumption",
            "applied_stage",
            "applied_approval_status",
            "consumed_effect",
            "system_consumption_action",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.deployment_rollout_intelligence_service import (
        DeploymentRolloutIntelligenceService,
    )

    service = DeploymentRolloutIntelligenceService()
    service.persisted_rollout_state_latest = lambda limit=20: {
        "status": "ok",
        "run_id": "run-dri04",
        "cycle_id": "cycle-dri04",
        "mode": "shadow",
        "consumed_run_id": "run-dri04:meta-next",
        "consumed_cycle_id": "cycle-dri04:meta-next",
        "items": [
            {
                "alpha_family": "trend",
                "rollout_state_id": "state-trend",
                "recommended_rollout_stage": "full",
                "rollout_eligibility": "eligible",
                "approval_status": "ready_for_review",
                "deployment_action": "prepare_full_rollout",
            },
            {
                "alpha_family": "event",
                "rollout_state_id": "state-event",
                "recommended_rollout_stage": "canary",
                "rollout_eligibility": "eligible",
                "approval_status": "ready_for_review",
                "deployment_action": "prepare_canary_rollout",
            },
            {
                "alpha_family": "carry",
                "rollout_state_id": "state-carry",
                "recommended_rollout_stage": "limited",
                "rollout_eligibility": "hold",
                "approval_status": "pending_evidence",
                "deployment_action": "hold_limited_rollout",
            },
        ],
        "cross_layer_coherence": {"coherent": True},
        "source_packets": {"deployment_rollout_intelligence": "DRI-03"},
        "rollout_decision_summary": {"family_count": 3},
        "candidate_docket_summary": {"family_count": 3},
        "persisted_rollout_state_summary": {"family_count": 3},
        "as_of": "2026-04-04T00:00:00+00:00",
    }

    payload = service.applied_rollout_consumption_latest(limit=20)
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")

    by_family = {str(item.get("alpha_family") or ""): item for item in list(payload.get("items") or [])}
    trend = by_family.get("trend", {})
    event = by_family.get("event", {})
    carry = by_family.get("carry", {})

    if str(trend.get("consumed_effect") or "") != "rollout_full_activation_applied":
        failures.append("trend_consumed_effect_invalid")
    if str(event.get("consumed_effect") or "") != "rollout_canary_activation_applied":
        failures.append("event_consumed_effect_invalid")
    if str(carry.get("consumed_effect") or "") != "rollout_limited_hold_applied":
        failures.append("carry_consumed_effect_invalid")
    if str(carry.get("applied_rollout_consumption", {}).get("applied_deployment_action") or "") != "hold_limited_rollout":
        failures.append("carry_applied_deployment_action_invalid")

    summary = payload.get("applied_rollout_consumption_summary") or {}
    if int(summary.get("family_count", 0) or 0) != 3:
        failures.append("summary_family_count_invalid")
    if int(summary.get("limited_consumptions", 0) or 0) != 1:
        failures.append("summary_limited_count_invalid")
    if int(summary.get("canary_consumptions", 0) or 0) != 1:
        failures.append("summary_canary_count_invalid")
    if int(summary.get("full_consumptions", 0) or 0) != 1:
        failures.append("summary_full_count_invalid")
    if str(summary.get("system_consumption_action") or "") != "apply_full_rollout_for_ready_families":
        failures.append("summary_system_consumption_action_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
