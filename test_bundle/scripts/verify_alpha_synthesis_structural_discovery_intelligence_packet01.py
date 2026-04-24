from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Alpha_synthesis_structural_discovery_intelligence_packet01_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_asd01_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/alpha-synthesis-candidates/latest",
            "/system/alpha-structure-search-state/latest",
            "/system/alpha-novelty-evaluation/latest",
            "/system/alpha-expression-library/latest",
            "/system/alpha-synthesis-effectiveness/latest",
        ]:
            if needle not in text:
                failures.append(f"plan_missing:{needle}")

    from ai_hedge_bot.alpha_synthesis.alpha_synthesis_service import AlphaSynthesisService
    from ai_hedge_bot.app.container import CONTAINER

    service = AlphaSynthesisService()
    store = CONTAINER.runtime_store
    for table in [
        "alpha_synthesis_novelty",
        "alpha_synthesis_candidates",
        "alpha_synthesis_runs",
        "alpha_expression_library",
        "alpha_experiments",
        "alpha_registry",
    ]:
        store.execute(f"DELETE FROM {table}")

    candidates = service.alpha_synthesis_candidates_latest(limit=10)
    search = service.alpha_structure_search_state_latest(limit=10)
    novelty = service.alpha_novelty_evaluation_latest(limit=10)
    library = service.alpha_expression_library_latest(limit=10)
    effectiveness = service.alpha_synthesis_effectiveness_latest(limit=10)

    if not list(candidates.get("items") or []):
        failures.append("missing_synthesis_candidates")
    if "search_state" not in search:
        failures.append("missing_search_state")
    if not list(novelty.get("items") or []):
        failures.append("missing_novelty_rows")
    if not list(library.get("items") or []):
        failures.append("missing_expression_library")
    effect = effectiveness.get("alpha_synthesis_effectiveness") or {}
    if str(effect.get("effectiveness_status") or "") not in {"effective", "watch", "insufficient"}:
        failures.append("invalid_effectiveness_status")
    if "system_alpha_synthesis_effectiveness_action" not in effect:
        failures.append("missing_effectiveness_action")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
