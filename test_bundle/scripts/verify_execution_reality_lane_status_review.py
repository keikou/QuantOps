from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
REVIEW_DOC = REPO_ROOT / "docs" / "Execution_reality_lane_status_review_2026-04-02.md"
PLANS_CURRENT = REPO_ROOT / "docs" / "03_plans" / "current.md"
TASKS_CURRENT = REPO_ROOT / "docs" / "04_tasks" / "current.md"


def main() -> None:
    failures: list[str] = []

    if not REVIEW_DOC.exists():
        failures.append("missing_lane_status_review_doc")
    else:
        text = REVIEW_DOC.read_text(encoding="utf-8")
        for needle in [
            "packet_01_to_10_defined_and_verified",
            "Packet 10: per-route execution leakage attribution is explicit for the latest run",
            "Execution Reality packet stack is coherent through Packet 10",
            "freeze this as the first `Execution Reality` checkpoint",
        ]:
            if needle not in text:
                failures.append(f"review_missing:{needle}")

    if not PLANS_CURRENT.exists():
        failures.append("missing_plans_current")
    else:
        plans_text = PLANS_CURRENT.read_text(encoding="utf-8")
        for needle in [
            "Current Packet 10 pair:",
            "Current Lane Review pair:",
            "Execution_reality_lane_status_review_2026-04-02.md",
        ]:
            if needle not in plans_text:
                failures.append(f"plans_missing:{needle}")

    if not TASKS_CURRENT.exists():
        failures.append("missing_tasks_current")
    else:
        tasks_text = TASKS_CURRENT.read_text(encoding="utf-8")
        for needle in [
            "current packet 10 = `per-route execution leakage attribution is explicit for the latest run`",
            "current review = `Execution Reality lane status review after Packet 10`",
        ]:
            if needle not in tasks_text:
                failures.append(f"tasks_missing:{needle}")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
