from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Alpha_evaluation_selection_intelligence_packet02_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []
    if not PLAN_DOC.exists():
        failures.append("missing_aes02_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/alpha-walk-forward/run",
            "/system/alpha-walk-forward/latest",
            "/system/alpha-walk-forward/candidate/{alpha_id}",
            "/system/alpha-oos-validation/latest",
            "/system/alpha-validation-decisions/latest",
            "/system/alpha-validation-failures/latest",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.alpha_validation.validation_service import AlphaValidationService

    service = AlphaValidationService()
    latest = service.latest(limit=10)
    decisions = service.alpha_validation_decisions_latest(limit=10)
    failures_payload = service.alpha_validation_failures_latest(limit=10)
    candidate = list(latest.get("items") or [])
    if not candidate:
        failures.append("missing_walk_forward_items")
    if not list(decisions.get("items") or []):
        failures.append("missing_validation_decisions")
    if "alpha_validation_decisions_summary" not in decisions:
        failures.append("missing_validation_decisions_summary")
    if "alpha_validation_failures_summary" not in failures_payload:
        failures.append("missing_validation_failures_summary")
    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
