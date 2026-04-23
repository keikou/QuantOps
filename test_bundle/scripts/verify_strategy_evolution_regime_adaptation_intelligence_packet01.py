from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Strategy_evolution_regime_adaptation_intelligence_packet01_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_seri01_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/regime-state/latest",
            "family_regime_state",
            "current_regime",
            "regime_confidence",
            "system_regime_action",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.strategy_evolution_regime_adaptation_intelligence_service import (
        StrategyEvolutionRegimeAdaptationIntelligenceService,
    )

    service = StrategyEvolutionRegimeAdaptationIntelligenceService()
    service.live_capital_control.control_effectiveness_latest = lambda limit=20: {
        "status": "ok",
        "run_id": "run-seri01",
        "cycle_id": "cycle-seri01",
        "mode": "live",
        "consumed_run_id": "run-seri01:lcc-next",
        "consumed_cycle_id": "cycle-seri01:lcc-next",
        "items": [
            {"alpha_family": "trend", "control_state": "live", "realized_effect": "beneficial", "live_control_action": "keep"},
            {"alpha_family": "carry", "control_state": "degraded", "realized_effect": "neutral", "live_control_action": "reduce"},
            {"alpha_family": "event", "control_state": "frozen", "realized_effect": "adverse", "live_control_action": "freeze"},
        ],
        "as_of": "2026-04-23T00:00:00+00:00",
    }
    service.meta_portfolio.efficiency_latest = lambda limit=20: {
        "status": "ok",
        "run_id": "run-seri01",
        "cycle_id": "cycle-seri01",
        "mode": "live",
        "consumed_run_id": "run-seri01:mpi-next",
        "consumed_cycle_id": "cycle-seri01:mpi-next",
        "items": [
            {"alpha_family": "trend", "realized_effect": "beneficial", "allocation_action": "shift_in"},
            {"alpha_family": "carry", "realized_effect": "neutral", "allocation_action": "hold"},
            {"alpha_family": "event", "realized_effect": "adverse", "allocation_action": "freeze"},
        ],
        "as_of": "2026-04-23T00:00:00+00:00",
    }
    service.research_promotion.persisted_governed_state_transitions_latest = lambda limit=20: {
        "status": "ok",
        "run_id": "run-seri01",
        "cycle_id": "cycle-seri01",
        "mode": "live",
        "items": [
            {"alpha_family": "trend", "new_governed_state": "promoted"},
            {"alpha_family": "carry", "new_governed_state": "candidate"},
            {"alpha_family": "event", "new_governed_state": "retired"},
        ],
        "as_of": "2026-04-23T00:00:00+00:00",
    }

    payload = service.latest(limit=20)
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")

    if str(payload.get("current_regime") or "") != "risk_off":
        failures.append("current_regime_invalid")
    if str(payload.get("system_regime_action") or "") != "gate_fragile_strategies":
        failures.append("system_regime_action_invalid")

    by_family = {str(item.get("alpha_family") or ""): item for item in list(payload.get("items") or [])}
    if str(by_family.get("trend", {}).get("family_regime_state") or "") != "risk_on":
        failures.append("trend_family_regime_invalid")
    if str(by_family.get("carry", {}).get("family_regime_state") or "") != "transition":
        failures.append("carry_family_regime_invalid")
    if str(by_family.get("event", {}).get("family_regime_state") or "") != "risk_off":
        failures.append("event_family_regime_invalid")

    summary = payload.get("regime_state_summary") or {}
    if int(summary.get("family_count", 0) or 0) != 3:
        failures.append("summary_family_count_invalid")
    if int(summary.get("risk_on_families", 0) or 0) != 1:
        failures.append("summary_risk_on_invalid")
    if int(summary.get("transition_families", 0) or 0) != 1:
        failures.append("summary_transition_invalid")
    if int(summary.get("risk_off_families", 0) or 0) != 1:
        failures.append("summary_risk_off_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
