from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Meta_portfolio_intelligence_cross_strategy_capital_allocation_packet01_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-mpi01-", dir=str(REPO_ROOT / "runtime")))

os.environ["AHB_RUNTIME_DIR"] = str(TEST_RUNTIME_DIR)

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_mpi01_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/meta-portfolio-allocation/latest",
            "current_allocation_share",
            "target_allocation_share",
            "marginal_efficiency_score",
            "allocation_action",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.meta_portfolio_intelligence_cross_strategy_capital_allocation_service import (
        MetaPortfolioIntelligenceCrossStrategyCapitalAllocationService,
    )

    service = MetaPortfolioIntelligenceCrossStrategyCapitalAllocationService()
    service.live_capital_control.control_effectiveness_latest = lambda limit=20: {
        "status": "ok",
        "run_id": "run-mpi01",
        "cycle_id": "cycle-mpi01",
        "mode": "live",
        "consumed_run_id": "run-mpi01:next",
        "consumed_cycle_id": "cycle-mpi01:next",
        "items": [
            {
                "alpha_family": "trend",
                "control_state": "live",
                "effective_live_capital": 1.0,
                "risk_budget_cap": 1.0,
                "realized_effect": "beneficial",
                "live_capital_control_consumption": {"utilization_ratio": 0.9},
            },
            {
                "alpha_family": "carry",
                "control_state": "degraded",
                "effective_live_capital": 0.5,
                "risk_budget_cap": 0.5,
                "realized_effect": "neutral",
                "live_capital_control_consumption": {"utilization_ratio": 0.8},
            },
            {
                "alpha_family": "event",
                "control_state": "frozen",
                "effective_live_capital": 0.0,
                "risk_budget_cap": 0.0,
                "realized_effect": "adverse",
                "live_capital_control_consumption": {"utilization_ratio": 0.0},
            },
        ],
        "cross_layer_coherence": {"coherent": True},
        "source_packets": {},
        "as_of": "2026-04-05T00:00:00+00:00",
    }
    service.portfolio.execution_aware_capital_allocation_latest = lambda: {
        "status": "ok",
        "items": [
            {"target_capital_multiplier": 1.0},
            {"target_capital_multiplier": 0.8},
        ],
    }

    payload = service.latest(limit=20)
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")

    by_family = {str(item.get("alpha_family") or ""): item for item in list(payload.get("items") or [])}
    if str(by_family.get("trend", {}).get("allocation_action") or "") != "shift_in":
        failures.append("trend_action_invalid")
    if str(by_family.get("carry", {}).get("allocation_action") or "") not in {"shift_out", "hold"}:
        failures.append("carry_action_invalid")
    if str(by_family.get("event", {}).get("allocation_action") or "") != "freeze":
        failures.append("event_action_invalid")
    if float(by_family.get("trend", {}).get("target_allocation_share", 0.0) or 0.0) <= float(
        by_family.get("trend", {}).get("current_allocation_share", 0.0) or 0.0
    ):
        failures.append("trend_target_share_not_increased")

    summary = payload.get("meta_portfolio_allocation_summary") or {}
    if int(summary.get("family_count", 0) or 0) != 3:
        failures.append("summary_family_count_invalid")
    if int(summary.get("shift_in_families", 0) or 0) < 1:
        failures.append("summary_shift_in_missing")
    if int(summary.get("frozen_families", 0) or 0) != 1:
        failures.append("summary_frozen_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
