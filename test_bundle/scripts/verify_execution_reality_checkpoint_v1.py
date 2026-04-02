from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "Execution_Reality_Checkpoint_v1.md"
PLANS_CURRENT = REPO_ROOT / "docs" / "03_plans" / "current.md"
TASKS_CURRENT = REPO_ROOT / "docs" / "04_tasks" / "current.md"
CURRENT_STATUS = REPO_ROOT / "docs" / "11_reports" / "current_status.md"


def main() -> None:
    failures: list[str] = []

    if not DOC.exists():
        failures.append("missing_execution_reality_checkpoint_v1_doc")
    else:
        text = DOC.read_text(encoding="utf-8")
        for needle in [
            "Status: `completed_and_verified`",
            "`A is correct`",
            "Packet 01 through Packet 10",
            "`execution is measurable, attributable, and economically explainable`",
            "average slippage by mode",
        ]:
            if needle not in text:
                failures.append(f"doc_missing:{needle}")

    if not PLANS_CURRENT.exists():
        failures.append("missing_plans_current")
    else:
        text = PLANS_CURRENT.read_text(encoding="utf-8")
        for needle in [
            "Current Checkpoint pair:",
            "Execution_Reality_Checkpoint_v1.md",
            "verify_execution_reality_checkpoint_v1.py",
        ]:
            if needle not in text:
                failures.append(f"plans_missing:{needle}")

    if not TASKS_CURRENT.exists():
        failures.append("missing_tasks_current")
    else:
        text = TASKS_CURRENT.read_text(encoding="utf-8")
        if "current checkpoint = `formalize Execution Reality v1 checkpoint`" not in text:
            failures.append("tasks_missing:current_checkpoint")

    if not CURRENT_STATUS.exists():
        failures.append("missing_current_status")
    else:
        text = CURRENT_STATUS.read_text(encoding="utf-8")
        if "`Execution Reality v1 checkpoint ready`" not in text:
            failures.append("current_status_missing:checkpoint_ready")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
