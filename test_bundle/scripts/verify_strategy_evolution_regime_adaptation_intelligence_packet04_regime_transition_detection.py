from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Strategy_evolution_regime_adaptation_intelligence_packet04_regime_transition_detection_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"
TEST_RUNTIME_DIR = REPO_ROOT / "runtime" / f"verify-seri04-{uuid.uuid4()}"
TEST_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

os.environ["AHB_RUNTIME_DIR"] = str(TEST_RUNTIME_DIR)

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_seri04_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/regime-transition-detection/latest",
            "transition_detected",
            "detection_strength",
            "previous_family_regime_state",
            "system_regime_transition_action",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.services.strategy_evolution_regime_adaptation_intelligence_service import (
        StrategyEvolutionRegimeAdaptationIntelligenceService,
    )

    service = StrategyEvolutionRegimeAdaptationIntelligenceService()
    service.strategy_gating_decision_latest = lambda limit=20: {
        "status": "ok",
        "run_id": "run-seri04",
        "cycle_id": "cycle-seri04",
        "mode": "live",
        "consumed_run_id": "run-seri04:gating-next",
        "consumed_cycle_id": "cycle-seri04:gating-next",
        "items": [
            {"alpha_family": "trend", "family_regime_state": "risk_on", "strategy_gating_decision": "allow"},
            {"alpha_family": "carry", "family_regime_state": "transition", "strategy_gating_decision": "shadow"},
            {"alpha_family": "event", "family_regime_state": "risk_off", "strategy_gating_decision": "retire"},
        ],
        "current_regime": "transition",
        "regime_confidence": 0.7,
        "supporting_signals": {"transition_families": 1},
        "system_regime_action": "observe_regime_shift_and_prepare_gating",
        "source_packets": {"strategy_evolution_regime_adaptation_intelligence": "SERI-03"},
        "regime_state_summary": {"family_count": 3},
        "strategy_regime_compatibility_summary": {"family_count": 3},
        "strategy_gating_decision_summary": {"family_count": 3},
        "as_of": "2026-04-23T00:00:00+00:00",
    }

    payload = service.regime_transition_detection_latest(limit=20)
    if payload.get("status") != "ok":
        failures.append("payload_status_not_ok")

    by_family = {str(item.get("alpha_family") or ""): item for item in list(payload.get("items") or [])}
    if bool((by_family.get("trend", {}).get("regime_transition_detection") or {}).get("transition_detected")):
        failures.append("trend_transition_invalid")
    if str((by_family.get("carry", {}).get("regime_transition_detection") or {}).get("detection_strength") or "") != "emerging":
        failures.append("carry_transition_invalid")
    if str((by_family.get("event", {}).get("regime_transition_detection") or {}).get("detection_strength") or "") != "emerging":
        failures.append("event_transition_invalid")

    summary = payload.get("regime_transition_detection_summary") or {}
    if int(summary.get("stable_families", 0) or 0) != 1:
        failures.append("summary_stable_invalid")
    if int(summary.get("emerging_transition_families", 0) or 0) != 2:
        failures.append("summary_emerging_invalid")
    if str(summary.get("system_regime_transition_action") or "") != "monitor_emerging_regime_transition":
        failures.append("summary_system_action_invalid")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
