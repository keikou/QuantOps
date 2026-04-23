from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Strategy_evolution_regime_adaptation_intelligence_packet05_strategy_survival_analysis_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_seri05_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/strategy-survival-analysis/latest",
            "survival_posture",
            "survival_reason",
            "survival_reason_codes",
            "system_strategy_survival_action",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.strategy_evolution_regime_adaptation_intelligence_service import (
        StrategyEvolutionRegimeAdaptationIntelligenceService,
    )

    service = StrategyEvolutionRegimeAdaptationIntelligenceService()
    service.regime_transition_detection_latest = lambda limit=20: {
        "status": "ok",
        "run_id": "run-seri05",
        "cycle_id": "cycle-seri05",
        "mode": "live",
        "consumed_run_id": "run-seri05:transition-next",
        "consumed_cycle_id": "cycle-seri05:transition-next",
        "items": [
            {
                "alpha_family": "trend",
                "strategy_gating_decision": "allow",
                "compatibility_score": 0.84,
                "family_regime_state": "risk_on",
                "regime_transition_detection": {"transition_detected": False, "detection_strength": "stable"},
            },
            {
                "alpha_family": "carry",
                "strategy_gating_decision": "shadow",
                "compatibility_score": 0.44,
                "family_regime_state": "transition",
                "regime_transition_detection": {"transition_detected": True, "detection_strength": "emerging"},
            },
            {
                "alpha_family": "event",
                "strategy_gating_decision": "retire",
                "compatibility_score": 0.18,
                "family_regime_state": "risk_off",
                "regime_transition_detection": {"transition_detected": True, "detection_strength": "confirmed"},
            },
        ],
        "current_regime": "transition",
        "regime_confidence": 0.7,
        "supporting_signals": {"transition_families": 1},
        "system_regime_action": "observe_regime_shift_and_prepare_gating",
        "source_packets": {"strategy_evolution_regime_adaptation_intelligence": "SERI-04"},
        "regime_state_summary": {"family_count": 3},
        "strategy_regime_compatibility_summary": {"family_count": 3},
        "strategy_gating_decision_summary": {"family_count": 3},
        "regime_transition_detection_summary": {"family_count": 3},
        "as_of": "2026-04-23T00:00:00+00:00",
    }

    payload = service.strategy_survival_analysis_latest(limit=20)
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")

    by_family = {str(item.get("alpha_family") or ""): item for item in list(payload.get("items") or [])}
    if str(((by_family.get("trend", {}).get("strategy_survival_analysis") or {}).get("survival_posture")) or "") != "sustain":
        failures.append("trend_survival_invalid")
    if str(((by_family.get("carry", {}).get("strategy_survival_analysis") or {}).get("survival_posture")) or "") != "watch":
        failures.append("carry_survival_invalid")
    if str(((by_family.get("event", {}).get("strategy_survival_analysis") or {}).get("survival_posture")) or "") != "retire":
        failures.append("event_survival_invalid")

    summary = payload.get("strategy_survival_analysis_summary") or {}
    if int(summary.get("sustain_families", 0) or 0) != 1:
        failures.append("summary_sustain_invalid")
    if int(summary.get("watch_families", 0) or 0) != 1:
        failures.append("summary_watch_invalid")
    if int(summary.get("retire_families", 0) or 0) != 1:
        failures.append("summary_retire_invalid")
    if str(summary.get("system_strategy_survival_action") or "") != "retire_non_surviving_strategies":
        failures.append("summary_system_action_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
