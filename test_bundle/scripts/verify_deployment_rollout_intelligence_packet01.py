from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Deployment_rollout_intelligence_packet01_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-dri01-", dir=str(REPO_ROOT / "runtime")))

os.environ["AHB_RUNTIME_DIR"] = str(TEST_RUNTIME_DIR)

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_dri01_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/deployment-rollout-decision/latest",
            "rollout_eligibility",
            "recommended_rollout_stage",
            "gating_conditions",
            "rollback_conditions",
            "system_rollout_action",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.deployment_rollout_intelligence_service import (
        DeploymentRolloutIntelligenceService,
    )

    service = DeploymentRolloutIntelligenceService()
    service.policy_optimization.outcome_effectiveness_latest = lambda limit=20: {
        "status": "ok",
        "run_id": "run-dri01",
        "cycle_id": "cycle-dri01",
        "mode": "shadow",
        "consumed_run_id": "run-dri01:meta-next",
        "consumed_cycle_id": "cycle-dri01:meta-next",
        "items": [
            {
                "alpha_family": "trend",
                "tuning_action": "reinforce",
                "consumed_effect": "meta_policy_reinforcement_applied",
                "intended_objective": "improve_meta_policy_quality",
                "realized_effect": "beneficial",
                "observed_policy_cycles": 5,
                "consumed_run_id": "run-dri01:meta-next",
                "consumed_cycle_id": "cycle-dri01:meta-next",
            },
            {
                "alpha_family": "carry",
                "tuning_action": "hold",
                "consumed_effect": "meta_policy_hold_applied",
                "intended_objective": "improve_meta_policy_quality",
                "realized_effect": "neutral",
                "observed_policy_cycles": 1,
                "consumed_run_id": "run-dri01:meta-next",
                "consumed_cycle_id": "cycle-dri01:meta-next",
            },
            {
                "alpha_family": "event",
                "tuning_action": "reinforce",
                "consumed_effect": "meta_policy_reinforcement_applied",
                "intended_objective": "improve_meta_policy_quality",
                "realized_effect": "beneficial",
                "observed_policy_cycles": 3,
                "consumed_run_id": "run-dri01:meta-next",
                "consumed_cycle_id": "cycle-dri01:meta-next",
            },
            {
                "alpha_family": "mean_reversion",
                "tuning_action": "retune",
                "consumed_effect": "meta_policy_retune_applied",
                "intended_objective": "improve_meta_policy_quality",
                "realized_effect": "adverse",
                "observed_policy_cycles": 2,
                "consumed_run_id": "run-dri01:meta-next",
                "consumed_cycle_id": "cycle-dri01:meta-next",
            },
        ],
        "cross_layer_coherence": {"coherent": True},
        "source_packets": {},
        "policy_effectiveness_summary": {"family_count": 4},
        "tuning_summary": {"family_count": 4},
        "persisted_meta_policy_summary": {"family_count": 4},
        "applied_tuning_consumption_summary": {"family_count": 4},
        "outcome_effectiveness_summary": {"family_count": 4},
        "as_of": "2026-04-04T00:00:00+00:00",
    }

    payload = service.latest(limit=20)
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")

    by_family = {str(item.get("alpha_family") or ""): item for item in list(payload.get("items") or [])}
    trend = by_family.get("trend", {})
    carry = by_family.get("carry", {})
    event = by_family.get("event", {})
    mean_reversion = by_family.get("mean_reversion", {})

    if str(trend.get("recommended_rollout_stage") or "") != "full":
        failures.append("trend_rollout_stage_invalid")
    if str(trend.get("rollout_eligibility") or "") != "eligible":
        failures.append("trend_eligibility_invalid")
    if str(carry.get("recommended_rollout_stage") or "") != "limited":
        failures.append("carry_rollout_stage_invalid")
    if str(carry.get("rollout_eligibility") or "") != "hold":
        failures.append("carry_eligibility_invalid")
    if str(event.get("recommended_rollout_stage") or "") != "canary":
        failures.append("event_rollout_stage_invalid")
    if str(mean_reversion.get("recommended_rollout_stage") or "") != "shadow":
        failures.append("mean_reversion_rollout_stage_invalid")
    if str(mean_reversion.get("rollout_eligibility") or "") != "blocked":
        failures.append("mean_reversion_eligibility_invalid")

    summary = payload.get("rollout_decision_summary") or {}
    if int(summary.get("family_count", 0) or 0) != 4:
        failures.append("summary_family_count_invalid")
    if int(summary.get("eligible_families", 0) or 0) != 2:
        failures.append("summary_eligible_count_invalid")
    if int(summary.get("hold_families", 0) or 0) != 1:
        failures.append("summary_hold_count_invalid")
    if int(summary.get("blocked_families", 0) or 0) != 1:
        failures.append("summary_blocked_count_invalid")
    if int(summary.get("shadow_families", 0) or 0) != 1:
        failures.append("summary_shadow_count_invalid")
    if int(summary.get("limited_families", 0) or 0) != 1:
        failures.append("summary_limited_count_invalid")
    if int(summary.get("canary_families", 0) or 0) != 1:
        failures.append("summary_canary_count_invalid")
    if int(summary.get("full_families", 0) or 0) != 1:
        failures.append("summary_full_count_invalid")
    if str(summary.get("system_rollout_action") or "") != "rollback_blocked_families_to_shadow":
        failures.append("summary_system_rollout_action_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
