from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Alpha_synthesis_structural_discovery_intelligence_packet04_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_asd04_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/alpha-hypothesis-agenda/latest",
            "/system/alpha-llm-hypothesis-prompts/latest",
            "/system/alpha-llm-translation-candidates/latest",
            "/system/alpha-hypothesis-critique/latest",
            "/system/alpha-hypothesis-effectiveness/latest",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.alpha_synthesis.alpha_synthesis_service import AlphaSynthesisService

    service = AlphaSynthesisService()
    service.alpha_regime_synthesis_agenda_latest = lambda limit=20: {
        "status": "ok",
        "current_regime": "transition",
        "regime_confidence": 0.74,
        "items": [
            {
                "alpha_family": "trend",
                "regime_bias": "expand",
                "preferred_features": ["returns", "volume"],
                "preferred_operators": ["rank", "ts_zscore"],
            },
            {
                "alpha_family": "carry",
                "regime_bias": "constrain",
                "preferred_features": ["spread_bps", "volatility"],
                "preferred_operators": ["winsorize", "cs_zscore"],
            },
        ],
        "as_of": "2026-04-24T00:00:00Z",
    }
    service.alpha_regime_expression_map_latest = lambda limit=20: {
        "status": "ok",
        "current_regime": "transition",
        "items": [
            {"alpha_family": "trend", "aligned_expressions": 2, "watch_expressions": 1, "misaligned_expressions": 0},
            {"alpha_family": "carry", "aligned_expressions": 0, "watch_expressions": 1, "misaligned_expressions": 2},
        ],
        "as_of": "2026-04-24T00:00:00Z",
    }
    service.alpha_llm_translation_candidates_latest = lambda limit=20: {
        "status": "ok",
        "current_regime": "transition",
        "items": [
            {
                "expression_id": "expr.h1",
                "validation_status": "accepted",
                "novelty_score": 0.81,
                "regime_bias": "expand",
                "preferred_features": ["returns", "volume"],
                "preferred_operators": ["rank", "ts_zscore"],
                "feature_set": ["returns", "volume"],
                "operator_set": ["rank", "ts_zscore"],
            },
            {
                "expression_id": "expr.h2",
                "validation_status": "rejected",
                "novelty_score": 0.42,
                "regime_bias": "constrain",
                "preferred_features": ["spread_bps", "volatility"],
                "preferred_operators": ["winsorize", "cs_zscore"],
                "feature_set": ["spread_bps"],
                "operator_set": ["winsorize"],
            },
        ],
        "alpha_llm_translation_candidates_summary": {
            "candidate_count": 2,
            "accepted_translations": 1,
            "rejected_translations": 1,
        },
        "as_of": "2026-04-24T00:00:00Z",
    }

    agenda = service.alpha_hypothesis_agenda_latest(limit=10)
    prompts = service.alpha_llm_hypothesis_prompts_latest(limit=10)
    critique = service.alpha_hypothesis_critique_latest(limit=10)
    effectiveness = service.alpha_hypothesis_effectiveness_latest(limit=10)

    if not list(agenda.get("items") or []):
        failures.append("missing_hypothesis_agenda")
    if not list(prompts.get("items") or []):
        failures.append("missing_hypothesis_prompts")
    if not list(critique.get("items") or []):
        failures.append("missing_hypothesis_critique")
    payload = effectiveness.get("alpha_hypothesis_effectiveness") or {}
    if str(payload.get("effectiveness_status") or "") not in {"effective", "watch", "insufficient"}:
        failures.append("invalid_hypothesis_effectiveness_status")
    if "system_alpha_hypothesis_effectiveness_action" not in payload:
        failures.append("missing_hypothesis_effectiveness_action")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
