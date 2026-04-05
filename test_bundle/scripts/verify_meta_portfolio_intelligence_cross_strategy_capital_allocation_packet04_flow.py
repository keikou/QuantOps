from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Meta_portfolio_intelligence_cross_strategy_capital_allocation_packet04_flow_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-mpi04-", dir=str(REPO_ROOT / "runtime")))

os.environ["AHB_RUNTIME_DIR"] = str(TEST_RUNTIME_DIR)

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_mpi04_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/meta-portfolio-flow/latest",
            "from_share",
            "to_share",
            "moved_share",
            "flow_action",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.meta_portfolio_intelligence_cross_strategy_capital_allocation_service import (
        MetaPortfolioIntelligenceCrossStrategyCapitalAllocationService,
    )

    service = MetaPortfolioIntelligenceCrossStrategyCapitalAllocationService()
    service.state_latest = lambda limit=20: {
        "status": "ok",
        "run_id": "run-mpi04",
        "cycle_id": "cycle-mpi04",
        "mode": "live",
        "consumed_run_id": "run-mpi04:next",
        "consumed_cycle_id": "cycle-mpi04:next",
        "items": [
            {
                "alpha_family": "trend",
                "meta_portfolio_state": "balanced",
                "meta_portfolio_decision": "hold",
                "current_allocation_share": 0.40,
                "target_allocation_share": 0.40,
            },
            {
                "alpha_family": "carry",
                "meta_portfolio_state": "concentrated",
                "meta_portfolio_decision": "shift",
                "current_allocation_share": 0.30,
                "target_allocation_share": 0.36,
            },
            {
                "alpha_family": "event",
                "meta_portfolio_state": "unstable",
                "meta_portfolio_decision": "rebalance",
                "current_allocation_share": 0.20,
                "target_allocation_share": 0.12,
            },
            {
                "alpha_family": "rv",
                "meta_portfolio_state": "frozen",
                "meta_portfolio_decision": "freeze",
                "current_allocation_share": 0.10,
                "target_allocation_share": 0.00,
            },
        ],
        "cross_layer_coherence": {"coherent": True},
        "source_packets": {},
        "meta_portfolio_allocation_summary": {"family_count": 4},
        "meta_portfolio_decision_summary": {"family_count": 4},
        "meta_portfolio_state_summary": {"family_count": 4},
        "as_of": "2026-04-05T00:00:00+00:00",
    }

    payload = service.flow_latest(limit=20)
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")

    by_family = {str(item.get("alpha_family") or ""): item for item in list(payload.get("items") or [])}
    if str(dict(by_family.get("carry", {}).get("meta_portfolio_flow") or {}).get("flow_action") or "") != "shift":
        failures.append("carry_flow_invalid")
    if str(dict(by_family.get("event", {}).get("meta_portfolio_flow") or {}).get("flow_action") or "") != "rebalance":
        failures.append("event_flow_invalid")
    if str(dict(by_family.get("rv", {}).get("meta_portfolio_flow") or {}).get("flow_action") or "") != "remove":
        failures.append("rv_flow_invalid")

    summary = payload.get("meta_portfolio_flow_summary") or {}
    if int(summary.get("family_count", 0) or 0) != 4:
        failures.append("summary_family_count_invalid")
    if int(summary.get("rebalance_flows", 0) or 0) != 1:
        failures.append("summary_rebalance_invalid")
    if int(summary.get("freeze_flows", 0) or 0) != 1:
        failures.append("summary_freeze_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
