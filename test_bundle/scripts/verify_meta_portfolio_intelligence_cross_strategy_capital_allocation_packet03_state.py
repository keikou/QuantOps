from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Meta_portfolio_intelligence_cross_strategy_capital_allocation_packet03_state_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-mpi03-", dir=str(REPO_ROOT / "runtime")))

os.environ["AHB_RUNTIME_DIR"] = str(TEST_RUNTIME_DIR)

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_mpi03_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/meta-portfolio-state/latest",
            "meta_portfolio_state",
            "meta_portfolio_state_id",
            "previous_meta_portfolio_state_id",
            "system_meta_portfolio_state_action",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.meta_portfolio_intelligence_cross_strategy_capital_allocation_service import (
        MetaPortfolioIntelligenceCrossStrategyCapitalAllocationService,
    )

    service = MetaPortfolioIntelligenceCrossStrategyCapitalAllocationService()
    service.decision_latest = lambda limit=20: {
        "status": "ok",
        "run_id": "run-mpi03",
        "cycle_id": "cycle-mpi03",
        "mode": "live",
        "consumed_run_id": "run-mpi03:next",
        "consumed_cycle_id": "cycle-mpi03:next",
        "items": [
            {
                "alpha_family": "trend",
                "meta_portfolio_decision": "hold",
                "capital_flow_hint": {"material_change": False},
            },
            {
                "alpha_family": "carry",
                "meta_portfolio_decision": "shift",
                "capital_flow_hint": {"material_change": False},
            },
            {
                "alpha_family": "event",
                "meta_portfolio_decision": "rebalance",
                "capital_flow_hint": {"material_change": True},
            },
            {
                "alpha_family": "rv",
                "meta_portfolio_decision": "freeze",
                "capital_flow_hint": {"material_change": True},
            },
        ],
        "cross_layer_coherence": {"coherent": True},
        "source_packets": {},
        "meta_portfolio_allocation_summary": {"family_count": 4},
        "meta_portfolio_decision_summary": {"family_count": 4},
        "as_of": "2026-04-05T00:00:00+00:00",
    }

    payload = service.state_latest(limit=20)
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")

    by_family = {str(item.get("alpha_family") or ""): item for item in list(payload.get("items") or [])}
    if str(by_family.get("trend", {}).get("meta_portfolio_state") or "") != "balanced":
        failures.append("trend_state_invalid")
    if str(by_family.get("carry", {}).get("meta_portfolio_state") or "") != "concentrated":
        failures.append("carry_state_invalid")
    if str(by_family.get("event", {}).get("meta_portfolio_state") or "") != "unstable":
        failures.append("event_state_invalid")
    if str(by_family.get("rv", {}).get("meta_portfolio_state") or "") != "frozen":
        failures.append("rv_state_invalid")

    summary = payload.get("meta_portfolio_state_summary") or {}
    if int(summary.get("family_count", 0) or 0) != 4:
        failures.append("summary_family_count_invalid")
    if int(summary.get("balanced_families", 0) or 0) != 1:
        failures.append("summary_balanced_invalid")
    if int(summary.get("concentrated_families", 0) or 0) != 1:
        failures.append("summary_concentrated_invalid")
    if int(summary.get("unstable_families", 0) or 0) != 1:
        failures.append("summary_unstable_invalid")
    if int(summary.get("frozen_families", 0) or 0) != 1:
        failures.append("summary_frozen_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
