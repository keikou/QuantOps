from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "Execution_reality_upward_report_2026-04-02.md"
CURRENT_STATUS = REPO_ROOT / "docs" / "11_reports" / "current_status.md"


def main() -> None:
    failures: list[str] = []

    if not DOC.exists():
        failures.append("missing_execution_reality_upward_report_doc")
    else:
        text = DOC.read_text(encoding="utf-8")
        for needle in [
            "ready_to_report_upward",
            "Packet 01 through Packet 10 defined and verified",
            "architect judgment aligned on `A`",
            "average slippage by mode",
            "treat subsequent work as optimization rather than checkpoint completion",
        ]:
            if needle not in text:
                failures.append(f"doc_missing:{needle}")

    if not CURRENT_STATUS.exists():
        failures.append("missing_current_status_doc")
    else:
        text = CURRENT_STATUS.read_text(encoding="utf-8")
        for needle in [
            "`baseline metrics v1 fixed from existing surfaces`",
            "`upward report is the current recommended next action`",
        ]:
            if needle not in text:
                failures.append(f"current_status_missing:{needle}")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
