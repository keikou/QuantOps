from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Alpha_synthesis_structural_discovery_intelligence_packet03_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_asd03_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/alpha-regime-synthesis-agenda/latest",
            "/system/alpha-regime-targeted-candidates/latest",
            "/system/alpha-regime-fit-evaluation/latest",
            "/system/alpha-regime-expression-map/latest",
            "/system/alpha-regime-synthesis-effectiveness/latest",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.alpha_synthesis.alpha_synthesis_service import AlphaSynthesisService

    service = AlphaSynthesisService()
    service.alpha_parent_candidates_latest = lambda limit=20: {
        "status": "ok",
        "items": [
            {"expression_id": "expr.trend.1", "formula": "rank(ts_zscore(returns, 10))", "feature_set": ["returns"], "operator_set": ["rank", "ts_zscore"]},
            {"expression_id": "expr.carry.1", "formula": "normalize(ts_mean(volume, 20))", "feature_set": ["volume"], "operator_set": ["normalize", "ts_mean"]},
        ],
    }
    service.alpha_mutation_candidates_latest = lambda limit=20: {
        "status": "ok",
        "items": [
            {"expression_id": "expr.m1", "feature_set": ["returns", "volume"], "operator_set": ["rank", "ts_zscore"], "validation_status": "accepted"},
            {"expression_id": "expr.m2", "feature_set": ["spread_bps"], "operator_set": ["winsorize"], "validation_status": "accepted"},
        ],
    }
    service.alpha_crossover_candidates_latest = lambda limit=20: {
        "status": "ok",
        "items": [
            {"expression_id": "expr.c1", "feature_set": ["returns"], "operator_set": ["rank", "ts_mean"], "validation_status": "accepted"},
            {"expression_id": "expr.c2", "feature_set": ["volatility"], "operator_set": ["cs_zscore"], "validation_status": "accepted"},
        ],
    }
    service.strategy_evolution.strategy_gating_decision_latest = lambda limit=20: {
        "status": "ok",
        "current_regime": "transition",
        "regime_confidence": 0.72,
        "items": [
            {"alpha_family": "trend", "family_regime_state": "risk_on", "strategy_gating_decision": "allow"},
            {"alpha_family": "carry", "family_regime_state": "transition", "strategy_gating_decision": "shadow"},
            {"alpha_family": "event", "family_regime_state": "risk_off", "strategy_gating_decision": "gate"},
        ],
        "as_of": "2026-04-24T00:00:00Z",
    }

    agenda = service.alpha_regime_synthesis_agenda_latest(limit=10)
    targeted = service.alpha_regime_targeted_candidates_latest(limit=10)
    fit = service.alpha_regime_fit_evaluation_latest(limit=10)
    expression_map = service.alpha_regime_expression_map_latest(limit=10)
    effectiveness = service.alpha_regime_synthesis_effectiveness_latest(limit=10)

    if not list(agenda.get("items") or []):
        failures.append("missing_regime_agenda")
    if not list(targeted.get("items") or []):
        failures.append("missing_regime_targeted_candidates")
    if not list(fit.get("items") or []):
        failures.append("missing_regime_fit_items")
    if not list(expression_map.get("items") or []):
        failures.append("missing_regime_expression_map")
    payload = effectiveness.get("alpha_regime_synthesis_effectiveness") or {}
    if str(payload.get("effectiveness_status") or "") not in {"effective", "watch", "insufficient"}:
        failures.append("invalid_regime_effectiveness_status")
    if "system_alpha_regime_synthesis_effectiveness_action" not in payload:
        failures.append("missing_regime_effectiveness_action")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
