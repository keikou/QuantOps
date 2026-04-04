from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Live_capital_control_adaptive_runtime_allocation_packet05_control_effectiveness_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-lcc05-", dir=str(REPO_ROOT / "runtime")))

os.environ["AHB_RUNTIME_DIR"] = str(TEST_RUNTIME_DIR)

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_lcc05_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/live-capital-control-effectiveness/latest",
            "intended_objective",
            "realized_effect",
            "effectiveness_reason_codes",
            "system_effectiveness_action",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.live_capital_control_adaptive_runtime_allocation_service import (
        LiveCapitalControlAdaptiveRuntimeAllocationService,
    )

    service = LiveCapitalControlAdaptiveRuntimeAllocationService()
    service.control_consumption_latest = lambda limit=20: {
        "status": "ok",
        "run_id": "run-lcc05",
        "cycle_id": "cycle-lcc05",
        "mode": "live",
        "consumed_run_id": "run-lcc05:live-next",
        "consumed_cycle_id": "cycle-lcc05:live-next",
        "items": [
            {
                "alpha_family": "trend",
                "control_state": "live",
                "live_capital_control_consumption": {"used_capital": 0.9, "used_risk": 0.9, "headroom": 0.1, "utilization_ratio": 0.9},
            },
            {
                "alpha_family": "carry",
                "control_state": "reduced",
                "live_capital_control_consumption": {"used_capital": 0.4, "used_risk": 0.4, "headroom": 0.1, "utilization_ratio": 0.8},
            },
            {
                "alpha_family": "event",
                "control_state": "degraded",
                "live_capital_control_consumption": {"used_capital": 0.6, "used_risk": 0.6, "headroom": -0.1, "utilization_ratio": 1.2},
            },
        ],
        "cross_layer_coherence": {"coherent": True},
        "source_packets": {},
        "live_capital_control_summary": {"family_count": 3},
        "live_capital_adjustment_summary": {"family_count": 3},
        "live_capital_control_state_summary": {"family_count": 3},
        "live_capital_control_consumption_summary": {"family_count": 3},
        "as_of": "2026-04-04T00:00:00+00:00",
    }

    payload = service.control_effectiveness_latest(limit=20)
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")

    by_family = {str(item.get("alpha_family") or ""): item for item in list(payload.get("items") or [])}
    if str(by_family.get("trend", {}).get("realized_effect") or "") != "beneficial":
        failures.append("trend_effect_invalid")
    if str(by_family.get("carry", {}).get("realized_effect") or "") != "neutral":
        failures.append("carry_effect_invalid")
    if str(by_family.get("event", {}).get("realized_effect") or "") != "adverse":
        failures.append("event_effect_invalid")

    summary = payload.get("live_capital_control_effectiveness_summary") or {}
    if int(summary.get("family_count", 0) or 0) != 3:
        failures.append("summary_family_count_invalid")
    if int(summary.get("beneficial_families", 0) or 0) != 1:
        failures.append("summary_beneficial_count_invalid")
    if int(summary.get("neutral_families", 0) or 0) != 1:
        failures.append("summary_neutral_count_invalid")
    if int(summary.get("adverse_families", 0) or 0) != 1:
        failures.append("summary_adverse_count_invalid")
    if str(summary.get("system_effectiveness_action") or "") != "rework_live_capital_control_policy":
        failures.append("summary_system_action_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
