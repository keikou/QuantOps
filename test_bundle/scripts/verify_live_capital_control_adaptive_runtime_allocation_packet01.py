from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Live_capital_control_adaptive_runtime_allocation_packet01_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-lcc01-", dir=str(REPO_ROOT / "runtime")))

os.environ["AHB_RUNTIME_DIR"] = str(TEST_RUNTIME_DIR)

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_lcc01_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/live-capital-control/latest",
            "effective_live_capital",
            "risk_budget_cap",
            "current_mode",
            "live_control_action",
            "system_live_capital_action",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.live_capital_control_adaptive_runtime_allocation_service import (
        LiveCapitalControlAdaptiveRuntimeAllocationService,
    )

    service = LiveCapitalControlAdaptiveRuntimeAllocationService()
    service.deployment_rollout.rollout_outcome_effectiveness_latest = lambda limit=20: {
        "status": "ok",
        "run_id": "run-lcc01",
        "cycle_id": "cycle-lcc01",
        "mode": "live",
        "consumed_run_id": "run-lcc01:rollout-next",
        "consumed_cycle_id": "cycle-lcc01:rollout-next",
        "items": [
            {"alpha_family": "trend", "recommended_rollout_stage": "full", "realized_effect": "beneficial"},
            {"alpha_family": "carry", "recommended_rollout_stage": "limited", "realized_effect": "neutral"},
            {"alpha_family": "event", "recommended_rollout_stage": "shadow", "realized_effect": "adverse"},
        ],
        "cross_layer_coherence": {"coherent": True},
        "as_of": "2026-04-04T00:00:00+00:00",
    }
    service.governance.cross_control_policy_arbitration_latest = lambda: {
        "status": "ok",
        "items": [{"resolved_runtime_action": "allow"}],
    }
    service.portfolio.execution_aware_capital_allocation_latest = lambda: {
        "status": "ok",
        "items": [{"target_capital_multiplier": 1.0}, {"target_capital_multiplier": 0.5}],
    }

    payload = service.latest(limit=20)
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")

    by_family = {str(item.get("alpha_family") or ""): item for item in list(payload.get("items") or [])}
    if str(by_family.get("trend", {}).get("current_mode") or "") != "live":
        failures.append("trend_mode_invalid")
    if str(by_family.get("carry", {}).get("current_mode") or "") != "degraded":
        failures.append("carry_mode_invalid")
    if str(by_family.get("event", {}).get("current_mode") or "") != "frozen":
        failures.append("event_mode_invalid")
    if float(by_family.get("event", {}).get("effective_live_capital", 1.0)) != 0.0:
        failures.append("event_capital_invalid")

    summary = payload.get("live_capital_control_summary") or {}
    if int(summary.get("family_count", 0) or 0) != 3:
        failures.append("summary_family_count_invalid")
    if int(summary.get("live_families", 0) or 0) != 1:
        failures.append("summary_live_count_invalid")
    if int(summary.get("degraded_families", 0) or 0) != 1:
        failures.append("summary_degraded_count_invalid")
    if int(summary.get("frozen_families", 0) or 0) != 1:
        failures.append("summary_frozen_count_invalid")
    if str(summary.get("system_live_capital_action") or "") != "freeze_stressed_live_capital":
        failures.append("summary_system_action_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
