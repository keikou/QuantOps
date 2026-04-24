from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Alpha_synthesis_structural_discovery_intelligence_packet02_plan.md"
V12_API_ROOT = REPO_ROOT / "apps" / "v12-api"

if str(V12_API_ROOT) not in sys.path:
    sys.path.insert(0, str(V12_API_ROOT))


def main() -> None:
    failures: list[str] = []

    if not PLAN_DOC.exists():
        failures.append("missing_asd02_plan_doc")
    else:
        text = PLAN_DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/alpha-parent-candidates/latest",
            "/system/alpha-mutation-candidates/latest",
            "/system/alpha-crossover-candidates/latest",
            "/system/alpha-evolution-search-state/latest",
            "/system/alpha-evolution-effectiveness/latest",
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

    service.alpha_synthesis_candidates_latest(limit=10)
    parents = service.alpha_parent_candidates_latest(limit=10)
    mutation = service.alpha_mutation_candidates_latest(limit=10)
    crossover = service.alpha_crossover_candidates_latest(limit=10)
    search_state = service.alpha_evolution_search_state_latest(limit=10)
    effectiveness = service.alpha_evolution_effectiveness_latest(limit=10)

    if not list(parents.get("items") or []):
        failures.append("missing_parent_candidates")
    if not list(mutation.get("items") or []):
        failures.append("missing_mutation_candidates")
    if not list(crossover.get("items") or []):
        failures.append("missing_crossover_candidates")
    if "search_state" not in search_state:
        failures.append("missing_evolution_search_state")
    payload = effectiveness.get("alpha_evolution_effectiveness") or {}
    if str(payload.get("effectiveness_status") or "") not in {"effective", "watch", "insufficient"}:
        failures.append("invalid_evolution_effectiveness_status")
    if "system_alpha_evolution_effectiveness_action" not in payload:
        failures.append("missing_evolution_effectiveness_action")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
