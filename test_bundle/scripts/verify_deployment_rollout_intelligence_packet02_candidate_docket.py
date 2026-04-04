from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Deployment_rollout_intelligence_packet02_candidate_docket_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-dri02-", dir=str(REPO_ROOT / "runtime")))

os.environ["AHB_RUNTIME_DIR"] = str(TEST_RUNTIME_DIR)

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_dri02_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/deployment-rollout-candidate-docket/latest",
            "approval_status",
            "docket_status",
            "deployment_action",
            "checkpoint_lineage",
            "system_docket_action",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.deployment_rollout_intelligence_service import (
        DeploymentRolloutIntelligenceService,
    )

    service = DeploymentRolloutIntelligenceService()
    service.latest = lambda limit=20: {
        "status": "ok",
        "run_id": "run-dri02",
        "cycle_id": "cycle-dri02",
        "mode": "shadow",
        "consumed_run_id": "run-dri02:meta-next",
        "consumed_cycle_id": "cycle-dri02:meta-next",
        "items": [
            {
                "alpha_family": "trend",
                "recommended_rollout_stage": "full",
                "rollout_eligibility": "eligible",
            },
            {
                "alpha_family": "event",
                "recommended_rollout_stage": "canary",
                "rollout_eligibility": "eligible",
            },
            {
                "alpha_family": "carry",
                "recommended_rollout_stage": "limited",
                "rollout_eligibility": "hold",
            },
            {
                "alpha_family": "mean_reversion",
                "recommended_rollout_stage": "shadow",
                "rollout_eligibility": "blocked",
            },
        ],
        "cross_layer_coherence": {"coherent": True},
        "source_packets": {"policy_optimization_meta_control_learning": "PO-05"},
        "rollout_decision_summary": {"family_count": 4},
        "as_of": "2026-04-04T00:00:00+00:00",
    }

    payload = service.candidate_docket_latest(limit=20)
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")

    by_family = {str(item.get("alpha_family") or ""): item for item in list(payload.get("items") or [])}
    trend = by_family.get("trend", {})
    event = by_family.get("event", {})
    carry = by_family.get("carry", {})
    mean_reversion = by_family.get("mean_reversion", {})

    if str(trend.get("docket_status") or "") != "full_rollout_candidate":
        failures.append("trend_docket_status_invalid")
    if str(trend.get("approval_status") or "") != "ready_for_review":
        failures.append("trend_approval_status_invalid")
    if str(event.get("deployment_action") or "") != "prepare_canary_rollout":
        failures.append("event_deployment_action_invalid")
    if str(carry.get("docket_status") or "") != "evidence_hold_candidate":
        failures.append("carry_docket_status_invalid")
    if str(carry.get("approval_status") or "") != "pending_evidence":
        failures.append("carry_approval_status_invalid")
    if str(mean_reversion.get("docket_status") or "") != "blocked_candidate":
        failures.append("mean_reversion_docket_status_invalid")
    if str(mean_reversion.get("approval_status") or "") != "denied":
        failures.append("mean_reversion_approval_status_invalid")

    summary = payload.get("candidate_docket_summary") or {}
    if int(summary.get("family_count", 0) or 0) != 4:
        failures.append("summary_family_count_invalid")
    if int(summary.get("ready_for_review_families", 0) or 0) != 2:
        failures.append("summary_ready_count_invalid")
    if int(summary.get("pending_evidence_families", 0) or 0) != 1:
        failures.append("summary_pending_count_invalid")
    if int(summary.get("denied_families", 0) or 0) != 1:
        failures.append("summary_denied_count_invalid")
    if str(summary.get("system_docket_action") or "") != "exclude_blocked_candidates_from_rollout_docket":
        failures.append("summary_system_docket_action_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
