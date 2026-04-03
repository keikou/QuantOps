from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "System_level_learning_feedback_integration_upward_report_2026-04-03.md"


def main() -> None:
    failures: list[str] = []

    if not DOC.exists():
        failures.append("missing_sllfi_upward_report")
    else:
        text = DOC.read_text(encoding="utf-8")
        for needle in [
            "SLLFI-05",
            "ready_for_upward_report",
            "consumed_run_id",
            "consumed_cycle_id",
            "Short Upward Statement",
        ]:
            if needle not in text:
                failures.append(f"doc_missing:{needle}")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
