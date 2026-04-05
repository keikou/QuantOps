from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Meta_portfolio_intelligence_cross_strategy_capital_allocation_packet05_efficiency_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="verify-mpi05-", dir=str(REPO_ROOT / "runtime")))

os.environ["AHB_RUNTIME_DIR"] = str(TEST_RUNTIME_DIR)

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_mpi05_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/meta-portfolio-efficiency/latest",
            "intended_objective",
            "realized_effect",
            "efficiency_reason_codes",
            "system_meta_portfolio_efficiency_action",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.meta_portfolio_intelligence_cross_strategy_capital_allocation_service import (
        MetaPortfolioIntelligenceCrossStrategyCapitalAllocationService,
    )

    service = MetaPortfolioIntelligenceCrossStrategyCapitalAllocationService()
    service.flow_latest = lambda limit=20: {
        "status": "ok",
        "run_id": "run-mpi05",
        "cycle_id": "cycle-mpi05",
        "mode": "live",
        "consumed_run_id": "run-mpi05:next",
        "consumed_cycle_id": "cycle-mpi05:next",
        "items": [
            {
                "alpha_family": "trend",
                "marginal_efficiency_score": 0.85,
                "meta_portfolio_flow": {"flow_action": "shift", "moved_share": 0.12},
            },
            {
                "alpha_family": "carry",
                "marginal_efficiency_score": 0.35,
                "meta_portfolio_flow": {"flow_action": "hold", "moved_share": 0.01},
            },
            {
                "alpha_family": "event",
                "marginal_efficiency_score": 0.30,
                "meta_portfolio_flow": {"flow_action": "rebalance", "moved_share": -0.14},
            },
        ],
        "cross_layer_coherence": {"coherent": True},
        "source_packets": {},
        "meta_portfolio_allocation_summary": {"family_count": 3},
        "meta_portfolio_decision_summary": {"family_count": 3},
        "meta_portfolio_state_summary": {"family_count": 3},
        "meta_portfolio_flow_summary": {"family_count": 3},
        "as_of": "2026-04-05T00:00:00+00:00",
    }

    payload = service.efficiency_latest(limit=20)
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")

    by_family = {str(item.get("alpha_family") or ""): item for item in list(payload.get("items") or [])}
    if str(by_family.get("trend", {}).get("realized_effect") or "") != "beneficial":
        failures.append("trend_effect_invalid")
    if str(by_family.get("carry", {}).get("realized_effect") or "") != "neutral":
        failures.append("carry_effect_invalid")
    if str(by_family.get("event", {}).get("realized_effect") or "") != "adverse":
        failures.append("event_effect_invalid")

    summary = payload.get("meta_portfolio_efficiency_summary") or {}
    if int(summary.get("family_count", 0) or 0) != 3:
        failures.append("summary_family_count_invalid")
    if int(summary.get("beneficial_families", 0) or 0) != 1:
        failures.append("summary_beneficial_invalid")
    if int(summary.get("neutral_families", 0) or 0) != 1:
        failures.append("summary_neutral_invalid")
    if int(summary.get("adverse_families", 0) or 0) != 1:
        failures.append("summary_adverse_invalid")
    if str(summary.get("system_meta_portfolio_efficiency_action") or "") != "rework_meta_portfolio_competition_policy":
        failures.append("summary_system_action_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
