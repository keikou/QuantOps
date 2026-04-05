from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Meta_portfolio_intelligence_cross_strategy_capital_allocation_packet02_decision_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-mpi02-", dir=str(REPO_ROOT / "runtime")))

os.environ["AHB_RUNTIME_DIR"] = str(TEST_RUNTIME_DIR)

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_mpi02_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/meta-portfolio-decision/latest",
            "meta_portfolio_decision",
            "decision_reason",
            "capital_flow_hint",
            "system_meta_portfolio_decision_action",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.meta_portfolio_intelligence_cross_strategy_capital_allocation_service import (
        MetaPortfolioIntelligenceCrossStrategyCapitalAllocationService,
    )

    service = MetaPortfolioIntelligenceCrossStrategyCapitalAllocationService()
    service.latest = lambda limit=20: {
        "status": "ok",
        "run_id": "run-mpi02",
        "cycle_id": "cycle-mpi02",
        "mode": "live",
        "consumed_run_id": "run-mpi02:next",
        "consumed_cycle_id": "cycle-mpi02:next",
        "items": [
            {
                "alpha_family": "trend",
                "current_allocation_share": 0.40,
                "target_allocation_share": 0.58,
                "allocation_share_delta": 0.18,
                "allocation_action": "shift_in",
            },
            {
                "alpha_family": "carry",
                "current_allocation_share": 0.35,
                "target_allocation_share": 0.30,
                "allocation_share_delta": -0.05,
                "allocation_action": "shift_out",
            },
            {
                "alpha_family": "event",
                "current_allocation_share": 0.25,
                "target_allocation_share": 0.12,
                "allocation_share_delta": -0.13,
                "allocation_action": "freeze",
            },
        ],
        "cross_layer_coherence": {"coherent": True},
        "source_packets": {},
        "meta_portfolio_allocation_summary": {"family_count": 3},
        "as_of": "2026-04-05T00:00:00+00:00",
    }

    payload = service.decision_latest(limit=20)
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")

    by_family = {str(item.get("alpha_family") or ""): item for item in list(payload.get("items") or [])}
    if str(by_family.get("trend", {}).get("meta_portfolio_decision") or "") != "rebalance":
        failures.append("trend_decision_invalid")
    if str(by_family.get("carry", {}).get("meta_portfolio_decision") or "") != "shift":
        failures.append("carry_decision_invalid")
    if str(by_family.get("event", {}).get("meta_portfolio_decision") or "") != "freeze":
        failures.append("event_decision_invalid")

    summary = payload.get("meta_portfolio_decision_summary") or {}
    if int(summary.get("family_count", 0) or 0) != 3:
        failures.append("summary_family_count_invalid")
    if int(summary.get("rebalance_families", 0) or 0) != 1:
        failures.append("summary_rebalance_invalid")
    if int(summary.get("freeze_families", 0) or 0) != 1:
        failures.append("summary_freeze_invalid")
    if str(summary.get("system_meta_portfolio_decision_action") or "") != "freeze_ineligible_meta_portfolio_families":
        failures.append("summary_system_action_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
