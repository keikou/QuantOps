from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Strategy_evolution_regime_adaptation_intelligence_packet02_strategy_regime_compatibility_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_seri02_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/strategy-regime-compatibility/latest",
            "compatibility_status",
            "compatibility_score",
            "recommended_posture",
            "system_strategy_regime_action",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.strategy_evolution_regime_adaptation_intelligence_service import (
        StrategyEvolutionRegimeAdaptationIntelligenceService,
    )

    service = StrategyEvolutionRegimeAdaptationIntelligenceService()
    service.latest = lambda limit=20: {
        "status": "ok",
        "run_id": "run-seri02",
        "cycle_id": "cycle-seri02",
        "mode": "live",
        "consumed_run_id": "run-seri02:regime-next",
        "consumed_cycle_id": "cycle-seri02:regime-next",
        "items": [
            {"alpha_family": "trend", "family_regime_state": "risk_on", "promotion_pressure": "expansion_pressure", "control_state": "live"},
            {"alpha_family": "carry", "family_regime_state": "transition", "promotion_pressure": "stable", "control_state": "degraded"},
            {"alpha_family": "event", "family_regime_state": "risk_off", "promotion_pressure": "transition_pressure", "control_state": "frozen"},
        ],
        "current_regime": "transition",
        "regime_confidence": 0.7,
        "supporting_signals": {"transition_families": 1},
        "system_regime_action": "observe_regime_shift_and_prepare_gating",
        "source_packets": {"strategy_evolution_regime_adaptation_intelligence": "SERI-01"},
        "regime_state_summary": {"family_count": 3},
        "as_of": "2026-04-23T00:00:00+00:00",
    }
    service.alpha_selection.effective_selection_slate_latest = lambda limit=20: {
        "status": "ok",
        "items": [
            {"alpha_family": "trend", "selection_score": 0.82},
            {"alpha_family": "carry", "selection_score": 0.57},
            {"alpha_family": "event", "selection_score": 0.2},
        ],
    }

    payload = service.strategy_regime_compatibility_latest(limit=20)
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")

    by_family = {str(item.get("alpha_family") or ""): item for item in list(payload.get("items") or [])}
    if str(by_family.get("trend", {}).get("compatibility_status") or "") != "compatible":
        failures.append("trend_compatibility_invalid")
    if str(by_family.get("carry", {}).get("compatibility_status") or "") != "watch":
        failures.append("carry_compatibility_invalid")
    if str(by_family.get("event", {}).get("compatibility_status") or "") != "incompatible":
        failures.append("event_compatibility_invalid")

    summary = payload.get("strategy_regime_compatibility_summary") or {}
    if int(summary.get("compatible_families", 0) or 0) != 1:
        failures.append("summary_compatible_invalid")
    if int(summary.get("watch_families", 0) or 0) != 1:
        failures.append("summary_watch_invalid")
    if int(summary.get("incompatible_families", 0) or 0) != 1:
        failures.append("summary_incompatible_invalid")
    if str(summary.get("system_strategy_regime_action") or "") != "identify_regime_incompatible_families":
        failures.append("summary_system_action_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
