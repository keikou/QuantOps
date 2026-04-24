from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAN_DOC = REPO_ROOT / "docs" / "Alpha_evaluation_selection_intelligence_packet05_plan.md"
TASK_DOC = REPO_ROOT / "docs" / "04_tasks" / "aes05_capacity_crowding_risk_2026-04-25.md"


def _contains(path: Path, needles: list[str], failures: list[str], prefix: str) -> None:
    if not path.exists():
        failures.append(f"missing:{path.name}")
        return
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            failures.append(f"{prefix}:{needle}")


def main() -> None:
    failures: list[str] = []
    needles = [
        "/system/alpha-capacity/run",
        "/system/alpha-capacity/latest",
        "/system/alpha-capacity/candidate/{alpha_id}",
        "/system/alpha-crowding/latest",
        "/system/alpha-impact/latest",
        "/system/alpha-capacity/ensemble/{ensemble_id}",
    ]
    _contains(PLAN_DOC, needles, failures, "plan_missing")
    _contains(TASK_DOC, needles, failures, "task_missing")
    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
