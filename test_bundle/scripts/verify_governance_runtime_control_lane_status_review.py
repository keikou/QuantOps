from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
REVIEW_DOC = REPO_ROOT / "docs" / "Governance_runtime_control_lane_status_review_2026-04-02.md"
PLANS_CURRENT = REPO_ROOT / "docs" / "03_plans" / "current.md"
TASKS_CURRENT = REPO_ROOT / "docs" / "04_tasks" / "current.md"
STATUS_DOC = REPO_ROOT / "docs" / "11_reports" / "current_status.md"


def main() -> None:
    failures: list[str] = []

    if not REVIEW_DOC.exists():
        failures.append("missing_governance_runtime_control_lane_review_doc")
    else:
        text = REVIEW_DOC.read_text(encoding="utf-8")
        for needle in [
            "Packet C6: competing control outputs resolve into one deterministic runtime action per route",
            "cross-control arbitration `resolved action / winning packet / explicit conflict set`",
            "Governance -> Runtime Control packet stack is coherent through Packet C6",
            "first `Governance -> Runtime Control` policy-coherent checkpoint",
        ]:
            if needle not in text:
                failures.append(f"review_missing:{needle}")

    if not PLANS_CURRENT.exists():
        failures.append("missing_plans_current")
    else:
        plans_text = PLANS_CURRENT.read_text(encoding="utf-8")
        for needle in [
            "Governance_runtime_control_lane_status_review_2026-04-02.md",
            "verify_governance_runtime_control_lane_status_review.py",
            "`C6: Cross-Control Policy Arbitration`",
            "`C5: Closed-Loop Adaptive Control`",
        ]:
            if needle not in plans_text:
                failures.append(f"plans_missing:{needle}")

    if not TASKS_CURRENT.exists():
        failures.append("missing_tasks_current")
    else:
        tasks_text = TASKS_CURRENT.read_text(encoding="utf-8")
        for needle in [
            "current packet C5 = `closed-loop adaptive control`",
            "current packet C6 = `cross-control policy arbitration`",
            "current review = `Governance -> Runtime Control lane status review after Packet C5`",
        ]:
            if needle not in tasks_text:
                failures.append(f"tasks_missing:{needle}")

    if not STATUS_DOC.exists():
        failures.append("missing_current_status_doc")
    else:
        status_text = STATUS_DOC.read_text(encoding="utf-8")
        for needle in [
            "`Governance -> Runtime Control` has reached a first verified checkpoint through Packet C6",
            "`route / guard / throttle / symbol capital control` surfaces are explicit",
            "`conflicting control outputs now resolve into one deterministic runtime action`",
            "Default Next Candidate",
        ]:
            if needle not in status_text:
                failures.append(f"status_missing:{needle}")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
