from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Deployment_rollout_intelligence_packet03_persisted_rollout_state_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-dri03-", dir=str(REPO_ROOT / "runtime")))

os.environ["AHB_RUNTIME_DIR"] = str(TEST_RUNTIME_DIR)

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_dri03_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/deployment-rollout-state/latest",
            "rollout_state_id",
            "previous_rollout_state_id",
            "deployment_action",
            "rollout_source_packet",
            "system_rollout_state_action",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.deployment_rollout_intelligence_service import (
        DeploymentRolloutIntelligenceService,
    )

    service = DeploymentRolloutIntelligenceService()
    service.candidate_docket_latest = lambda limit=20: {
        "status": "ok",
        "run_id": "run-dri03",
        "cycle_id": "cycle-dri03",
        "mode": "shadow",
        "consumed_run_id": "run-dri03:meta-next",
        "consumed_cycle_id": "cycle-dri03:meta-next",
        "items": [
            {
                "alpha_family": "trend",
                "recommended_rollout_stage": "full",
                "rollout_eligibility": "eligible",
                "approval_status": "ready_for_review",
                "docket_status": "full_rollout_candidate",
                "deployment_action": "prepare_full_rollout",
                "rollout_priority": "high",
            },
            {
                "alpha_family": "carry",
                "recommended_rollout_stage": "limited",
                "rollout_eligibility": "hold",
                "approval_status": "pending_evidence",
                "docket_status": "evidence_hold_candidate",
                "deployment_action": "hold_limited_rollout",
                "rollout_priority": "normal",
            },
        ],
        "cross_layer_coherence": {"coherent": True},
        "source_packets": {"deployment_rollout_intelligence": "DRI-02"},
        "rollout_decision_summary": {"family_count": 2},
        "candidate_docket_summary": {"family_count": 2},
        "as_of": "2026-04-04T00:00:00+00:00",
    }

    payload = service.persisted_rollout_state_latest(limit=20)
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")

    by_family = {str(item.get("alpha_family") or ""): item for item in list(payload.get("items") or [])}
    trend = by_family.get("trend", {})
    carry = by_family.get("carry", {})

    if not str(trend.get("rollout_state_id") or ""):
        failures.append("trend_rollout_state_id_missing")
    if str(trend.get("rollout_source_packet") or "") != "DRI-02":
        failures.append("trend_rollout_source_packet_invalid")
    if str(carry.get("deployment_action") or "") != "hold_limited_rollout":
        failures.append("carry_deployment_action_invalid")
    if str(carry.get("approval_status") or "") != "pending_evidence":
        failures.append("carry_approval_status_invalid")

    summary = payload.get("persisted_rollout_state_summary") or {}
    if int(summary.get("family_count", 0) or 0) != 2:
        failures.append("summary_family_count_invalid")
    if int(summary.get("persisted_states", 0) or 0) != 2:
        failures.append("summary_persisted_states_invalid")
    if str(summary.get("system_rollout_state_action") or "") != "persist_rollout_candidate_state":
        failures.append("summary_system_rollout_state_action_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
