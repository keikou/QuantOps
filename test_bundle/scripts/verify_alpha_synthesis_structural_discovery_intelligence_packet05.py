from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Alpha_synthesis_structural_discovery_intelligence_packet05_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_asd05_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/alpha-hypothesis-feedback-queue/latest",
            "/system/alpha-hypothesis-prompt-tuning/latest",
            "/system/alpha-synthesis-policy-updates/latest",
            "/system/alpha-feedback-learning-state/latest",
            "/system/alpha-feedback-optimization-effectiveness/latest",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.alpha_synthesis.alpha_synthesis_service import AlphaSynthesisService

    service = AlphaSynthesisService()
    service.alpha_hypothesis_critique_latest = lambda limit=20: {
        "status": "ok",
        "current_regime": "transition",
        "items": [
            {
                "brief_id": "hypothesis.trend.expand.1",
                "expression_id": "expr.good",
                "alpha_family": "trend",
                "regime_bias": "expand",
                "hypothesis_critique_status": "strong",
                "hypothesis_critique_score": 0.83,
            },
            {
                "brief_id": "hypothesis.carry.constrain.1",
                "expression_id": "expr.watch",
                "alpha_family": "carry",
                "regime_bias": "constrain",
                "hypothesis_critique_status": "watch",
                "hypothesis_critique_score": 0.62,
            },
        ],
        "as_of": "2026-04-24T00:00:00Z",
    }
    service.alpha_hypothesis_effectiveness_latest = lambda limit=20: {
        "status": "ok",
        "current_regime": "transition",
        "alpha_hypothesis_effectiveness": {
            "effectiveness_status": "watch",
            "prompt_count": 2,
            "accepted_translation_count": 1,
            "strong_candidate_count": 1,
        },
        "as_of": "2026-04-24T00:00:00Z",
    }

    queue = service.alpha_hypothesis_feedback_queue_latest(limit=10)
    tuning = service.alpha_hypothesis_prompt_tuning_latest(limit=10)
    updates = service.alpha_synthesis_policy_updates_latest(limit=10)
    state = service.alpha_feedback_learning_state_latest(limit=10)
    effectiveness = service.alpha_feedback_optimization_effectiveness_latest(limit=10)

    if not list(queue.get("items") or []):
        failures.append("missing_feedback_queue")
    if not list(tuning.get("items") or []):
        failures.append("missing_prompt_tuning")
    if not list(updates.get("items") or []):
        failures.append("missing_policy_updates")
    payload = state.get("feedback_learning_state") or {}
    if str(payload.get("learning_state") or "") not in {"active_feedback_learning", "idle_feedback_learning", "corrective_feedback_learning"}:
        failures.append("invalid_feedback_learning_state")
    optimization_payload = effectiveness.get("alpha_feedback_optimization_effectiveness") or {}
    if str(optimization_payload.get("effectiveness_status") or "") not in {"effective", "watch", "insufficient"}:
        failures.append("invalid_feedback_optimization_effectiveness_status")
    if "system_alpha_feedback_optimization_action" not in optimization_payload:
        failures.append("missing_feedback_optimization_action")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
