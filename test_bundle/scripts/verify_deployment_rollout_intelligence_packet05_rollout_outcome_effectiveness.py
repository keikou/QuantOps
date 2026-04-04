from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Deployment_rollout_intelligence_packet05_rollout_outcome_effectiveness_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-dri05-", dir=str(REPO_ROOT / "runtime")))

os.environ["AHB_RUNTIME_DIR"] = str(TEST_RUNTIME_DIR)

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_dri05_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/deployment-rollout-effectiveness/latest",
            "intended_objective",
            "realized_effect",
            "effectiveness_reason_codes",
            "system_effectiveness_action",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.deployment_rollout_intelligence_service import (
        DeploymentRolloutIntelligenceService,
    )

    service = DeploymentRolloutIntelligenceService()
    service.applied_rollout_consumption_latest = lambda limit=20: {
        "status": "ok",
        "run_id": "run-dri05",
        "cycle_id": "cycle-dri05",
        "mode": "shadow",
        "consumed_run_id": "run-dri05:rollout-next",
        "consumed_cycle_id": "cycle-dri05:rollout-next",
        "items": [
            {
                "alpha_family": "trend",
                "recommended_rollout_stage": "full",
                "rollout_eligibility": "eligible",
                "consumed_effect": "rollout_full_activation_applied",
            },
            {
                "alpha_family": "event",
                "recommended_rollout_stage": "canary",
                "rollout_eligibility": "eligible",
                "consumed_effect": "rollout_canary_activation_applied",
            },
            {
                "alpha_family": "carry",
                "recommended_rollout_stage": "limited",
                "rollout_eligibility": "hold",
                "consumed_effect": "rollout_limited_hold_applied",
            },
            {
                "alpha_family": "mean_reversion",
                "recommended_rollout_stage": "shadow",
                "rollout_eligibility": "blocked",
                "consumed_effect": "rollout_shadow_hold_applied",
            },
        ],
        "cross_layer_coherence": {"coherent": True},
        "source_packets": {"deployment_rollout_intelligence": "DRI-04"},
        "rollout_decision_summary": {"family_count": 4},
        "candidate_docket_summary": {"family_count": 4},
        "persisted_rollout_state_summary": {"family_count": 4},
        "applied_rollout_consumption_summary": {"family_count": 4},
        "as_of": "2026-04-04T00:00:00+00:00",
    }

    payload = service.rollout_outcome_effectiveness_latest(limit=20)
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")

    by_family = {str(item.get("alpha_family") or ""): item for item in list(payload.get("items") or [])}
    if str(by_family.get("trend", {}).get("realized_effect") or "") != "beneficial":
        failures.append("trend_realized_effect_invalid")
    if str(by_family.get("event", {}).get("realized_effect") or "") != "beneficial":
        failures.append("event_realized_effect_invalid")
    if str(by_family.get("carry", {}).get("realized_effect") or "") != "neutral":
        failures.append("carry_realized_effect_invalid")
    if str(by_family.get("mean_reversion", {}).get("realized_effect") or "") != "adverse":
        failures.append("mean_reversion_realized_effect_invalid")

    summary = payload.get("rollout_outcome_effectiveness_summary") or {}
    if int(summary.get("family_count", 0) or 0) != 4:
        failures.append("summary_family_count_invalid")
    if int(summary.get("beneficial_families", 0) or 0) != 2:
        failures.append("summary_beneficial_count_invalid")
    if int(summary.get("neutral_families", 0) or 0) != 1:
        failures.append("summary_neutral_count_invalid")
    if int(summary.get("adverse_families", 0) or 0) != 1:
        failures.append("summary_adverse_count_invalid")
    if str(summary.get("system_effectiveness_action") or "") != "rework_adverse_rollout_posture":
        failures.append("summary_system_effectiveness_action_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
