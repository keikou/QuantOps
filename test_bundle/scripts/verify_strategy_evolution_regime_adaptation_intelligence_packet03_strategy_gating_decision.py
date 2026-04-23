from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Strategy_evolution_regime_adaptation_intelligence_packet03_strategy_gating_decision_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_seri03_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/strategy-gating-decision/latest",
            "strategy_gating_decision",
            "gating_reason",
            "gating_reason_codes",
            "system_strategy_gating_action",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.strategy_evolution_regime_adaptation_intelligence_service import (
        StrategyEvolutionRegimeAdaptationIntelligenceService,
    )

    service = StrategyEvolutionRegimeAdaptationIntelligenceService()
    service.strategy_regime_compatibility_latest = lambda limit=20: {
        "status": "ok",
        "run_id": "run-seri03",
        "cycle_id": "cycle-seri03",
        "mode": "live",
        "consumed_run_id": "run-seri03:compat-next",
        "consumed_cycle_id": "cycle-seri03:compat-next",
        "items": [
            {"alpha_family": "trend", "compatibility_status": "compatible", "recommended_posture": "allow", "promotion_pressure": "expansion_pressure", "family_regime_state": "risk_on", "compatibility_score": 0.84},
            {"alpha_family": "carry", "compatibility_status": "watch", "recommended_posture": "shadow_or_reduce", "promotion_pressure": "stable", "family_regime_state": "transition", "compatibility_score": 0.44},
            {"alpha_family": "event", "compatibility_status": "incompatible", "recommended_posture": "gate", "promotion_pressure": "transition_pressure", "family_regime_state": "risk_off", "compatibility_score": 0.18},
        ],
        "current_regime": "transition",
        "regime_confidence": 0.7,
        "supporting_signals": {"transition_families": 1},
        "system_regime_action": "observe_regime_shift_and_prepare_gating",
        "source_packets": {"strategy_evolution_regime_adaptation_intelligence": "SERI-02"},
        "regime_state_summary": {"family_count": 3},
        "strategy_regime_compatibility_summary": {"family_count": 3},
        "as_of": "2026-04-23T00:00:00+00:00",
    }

    payload = service.strategy_gating_decision_latest(limit=20)
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")

    by_family = {str(item.get("alpha_family") or ""): item for item in list(payload.get("items") or [])}
    if str(by_family.get("trend", {}).get("strategy_gating_decision") or "") != "allow":
        failures.append("trend_gating_invalid")
    if str(by_family.get("carry", {}).get("strategy_gating_decision") or "") != "shadow":
        failures.append("carry_gating_invalid")
    if str(by_family.get("event", {}).get("strategy_gating_decision") or "") != "retire":
        failures.append("event_gating_invalid")

    summary = payload.get("strategy_gating_decision_summary") or {}
    if int(summary.get("allow_families", 0) or 0) != 1:
        failures.append("summary_allow_invalid")
    if int(summary.get("shadow_families", 0) or 0) != 1:
        failures.append("summary_shadow_invalid")
    if int(summary.get("retire_families", 0) or 0) != 1:
        failures.append("summary_retire_invalid")
    if str(summary.get("system_strategy_gating_action") or "") != "retire_regime_broken_families":
        failures.append("summary_system_action_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
