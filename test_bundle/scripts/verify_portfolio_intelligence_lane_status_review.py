from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "Portfolio_intelligence_lane_status_review_2026-04-02.md"
PLANS_CURRENT = REPO_ROOT / "docs" / "03_plans" / "current.md"
TASKS_CURRENT = REPO_ROOT / "docs" / "04_tasks" / "current.md"
STATUS_DOC = REPO_ROOT / "docs" / "11_reports" / "current_status.md"


def main() -> None:
    failures: list[str] = []

    if not DOC.exists():
        failures.append("missing_portfolio_intelligence_lane_review_doc")
    else:
        text = DOC.read_text(encoding="utf-8")
        for needle in [
            "Packet PI-03: latest exposure shaping is explicitly comparable to the previous run",
            "Packet PI-04: competing allocation pressures now resolve into one deterministic portfolio allocation action per symbol",
            "Packet PI-05: previous resolved allocation actions are explicitly evaluated against the next run's realized portfolio response",
            "portfolio-level policy effectiveness summary",
            "Portfolio Intelligence has reached a coherent first packet set",
            "first `Portfolio Intelligence` outcome-evaluable checkpoint",
        ]:
            if needle not in text:
                failures.append(f"doc_missing:{needle}")

    if not PLANS_CURRENT.exists():
        failures.append("missing_plans_current")
    else:
        text = PLANS_CURRENT.read_text(encoding="utf-8")
        for needle in [
            "Portfolio_intelligence_packet01_execution_aware_capital_allocation_plan.md",
            "Portfolio_intelligence_packet02_execution_aware_exposure_shaping_plan.md",
            "Portfolio_intelligence_packet03_allocation_stability_plan.md",
            "Portfolio_intelligence_packet04_allocation_tradeoff_resolution_plan.md",
            "Portfolio_intelligence_packet05_allocation_outcome_effectiveness_plan.md",
            "verify_portfolio_intelligence_packet01_execution_aware_capital_allocation.py",
            "verify_portfolio_intelligence_packet02_execution_aware_exposure_shaping.py",
            "verify_portfolio_intelligence_packet03_allocation_stability.py",
            "verify_portfolio_intelligence_packet04_allocation_tradeoff_resolution.py",
            "verify_portfolio_intelligence_packet05_allocation_outcome_effectiveness.py",
            "`PI-01: Execution-Aware Capital Allocation Surface`",
            "`PI-02: Execution-Aware Exposure Shaping`",
            "`PI-03: Allocation Stability Across Runs`",
            "`PI-04: Allocation Tradeoff Resolution`",
            "`PI-05: Allocation Outcome Effectiveness`",
        ]:
            if needle not in text:
                failures.append(f"plans_missing:{needle}")

    if not TASKS_CURRENT.exists():
        failures.append("missing_tasks_current")
    else:
        text = TASKS_CURRENT.read_text(encoding="utf-8")
        for needle in [
            "current packet PI-01 = `execution-aware capital allocation surface`",
            "current packet PI-02 = `execution-aware exposure shaping`",
            "current packet PI-03 = `allocation stability across runs`",
            "current packet PI-04 = `allocation tradeoff resolution`",
            "current packet PI-05 = `allocation outcome effectiveness`",
            "current dependency = `Governance -> Runtime Control v1 checkpoint through C6`",
        ]:
            if needle not in text:
                failures.append(f"tasks_missing:{needle}")

    if not STATUS_DOC.exists():
        failures.append("missing_current_status_doc")
    else:
        text = STATUS_DOC.read_text(encoding="utf-8")
        for needle in [
            "`Portfolio Intelligence` has reached a first checkpoint through Packet PI-05",
            "`capital allocation is no longer execution-blind`",
            "`portfolio actions are now evaluable against realized next-run effectiveness`",
            "Portfolio_intelligence_lane_status_review_2026-04-02.md",
        ]:
            if needle not in text:
                failures.append(f"status_missing:{needle}")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
