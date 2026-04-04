from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Live_capital_control_adaptive_runtime_allocation_packet03_control_state_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-lcc03-", dir=str(REPO_ROOT / "runtime")))

os.environ["AHB_RUNTIME_DIR"] = str(TEST_RUNTIME_DIR)

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_lcc03_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/live-capital-control-state/latest",
            "control_state_id",
            "previous_control_state_id",
            "decision_age_seconds",
            "stale_flag",
            "system_control_state_action",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.live_capital_control_adaptive_runtime_allocation_service import (
        LiveCapitalControlAdaptiveRuntimeAllocationService,
    )

    service = LiveCapitalControlAdaptiveRuntimeAllocationService()
    service.adjustment_decision_latest = lambda limit=20: {
        "status": "ok",
        "run_id": "run-lcc03",
        "cycle_id": "cycle-lcc03",
        "mode": "live",
        "consumed_run_id": "run-lcc03:rollout-next",
        "consumed_cycle_id": "cycle-lcc03:rollout-next",
        "items": [
            {"alpha_family": "trend", "current_mode": "live", "capital_adjustment_decision": "scale_up", "effective_live_capital": 1.0, "risk_budget_cap": 1.0},
            {"alpha_family": "carry", "current_mode": "degraded", "capital_adjustment_decision": "scale_down", "effective_live_capital": 0.5, "risk_budget_cap": 0.5},
            {"alpha_family": "event", "current_mode": "frozen", "capital_adjustment_decision": "freeze", "effective_live_capital": 0.0, "risk_budget_cap": 0.0},
        ],
        "cross_layer_coherence": {"coherent": True},
        "source_packets": {},
        "live_capital_control_summary": {"family_count": 3},
        "live_capital_adjustment_summary": {"family_count": 3},
        "as_of": "2026-04-04T00:00:00+00:00",
    }

    payload = service.control_state_latest(limit=20)
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")

    by_family = {str(item.get("alpha_family") or ""): item for item in list(payload.get("items") or [])}
    if str(by_family.get("trend", {}).get("control_state") or "") != "live":
        failures.append("trend_state_invalid")
    if str(by_family.get("carry", {}).get("control_state") or "") != "reduced":
        failures.append("carry_state_invalid")
    if str(by_family.get("event", {}).get("control_state") or "") != "frozen":
        failures.append("event_state_invalid")
    if not str(by_family.get("trend", {}).get("control_state_id") or ""):
        failures.append("trend_state_id_missing")

    summary = payload.get("live_capital_control_state_summary") or {}
    if int(summary.get("family_count", 0) or 0) != 3:
        failures.append("summary_family_count_invalid")
    if int(summary.get("live_families", 0) or 0) != 1:
        failures.append("summary_live_count_invalid")
    if int(summary.get("reduced_families", 0) or 0) != 1:
        failures.append("summary_reduced_count_invalid")
    if int(summary.get("frozen_families", 0) or 0) != 1:
        failures.append("summary_frozen_count_invalid")
    if str(summary.get("system_control_state_action") or "") != "persist_live_capital_control_state":
        failures.append("summary_system_action_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
