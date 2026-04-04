from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Live_capital_control_adaptive_runtime_allocation_packet02_adjustment_decision_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-lcc02-", dir=str(REPO_ROOT / "runtime")))

os.environ["AHB_RUNTIME_DIR"] = str(TEST_RUNTIME_DIR)

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_lcc02_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/live-capital-adjustment-decision/latest",
            "capital_adjustment_decision",
            "decision_reason",
            "scale_up",
            "revert_to_shadow",
            "system_adjustment_action",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.live_capital_control_adaptive_runtime_allocation_service import (
        LiveCapitalControlAdaptiveRuntimeAllocationService,
    )

    service = LiveCapitalControlAdaptiveRuntimeAllocationService()
    service.latest = lambda limit=20: {
        "status": "ok",
        "run_id": "run-lcc02",
        "cycle_id": "cycle-lcc02",
        "mode": "live",
        "consumed_run_id": "run-lcc02:rollout-next",
        "consumed_cycle_id": "cycle-lcc02:rollout-next",
        "items": [
            {"alpha_family": "trend", "current_mode": "live", "recommended_rollout_stage": "full", "realized_effect": "beneficial", "effective_live_capital": 1.0},
            {"alpha_family": "carry", "current_mode": "degraded", "recommended_rollout_stage": "limited", "realized_effect": "neutral", "effective_live_capital": 0.5},
            {"alpha_family": "event", "current_mode": "frozen", "recommended_rollout_stage": "shadow", "realized_effect": "adverse", "effective_live_capital": 0.0},
        ],
        "cross_layer_coherence": {"coherent": True},
        "source_packets": {},
        "live_capital_control_summary": {"family_count": 3},
        "as_of": "2026-04-04T00:00:00+00:00",
    }

    payload = service.adjustment_decision_latest(limit=20)
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")

    by_family = {str(item.get("alpha_family") or ""): item for item in list(payload.get("items") or [])}
    if str(by_family.get("trend", {}).get("capital_adjustment_decision") or "") != "scale_up":
        failures.append("trend_decision_invalid")
    if str(by_family.get("carry", {}).get("capital_adjustment_decision") or "") != "scale_down":
        failures.append("carry_decision_invalid")
    if str(by_family.get("event", {}).get("capital_adjustment_decision") or "") != "revert_to_shadow":
        failures.append("event_decision_invalid")

    summary = payload.get("live_capital_adjustment_summary") or {}
    if int(summary.get("family_count", 0) or 0) != 3:
        failures.append("summary_family_count_invalid")
    if int(summary.get("scale_up_families", 0) or 0) != 1:
        failures.append("summary_scale_up_count_invalid")
    if int(summary.get("scale_down_families", 0) or 0) != 1:
        failures.append("summary_scale_down_count_invalid")
    if int(summary.get("revert_to_shadow_families", 0) or 0) != 1:
        failures.append("summary_revert_count_invalid")
    if str(summary.get("system_adjustment_action") or "") != "revert_stressed_live_allocations_to_shadow":
        failures.append("summary_system_action_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
