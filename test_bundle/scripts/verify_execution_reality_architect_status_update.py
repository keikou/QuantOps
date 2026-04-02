from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "Execution_reality_architect_status_update_2026-04-02.md"
CURRENT_STATUS = REPO_ROOT / "docs" / "11_reports" / "current_status.md"


def main() -> None:
    failures: list[str] = []

    if not DOC.exists():
        failures.append("missing_execution_reality_architect_status_update_doc")
    else:
        text = DOC.read_text(encoding="utf-8")
        for needle in [
            "checkpoint_ready_for_architect_review",
            "Packet 10: per-route execution leakage attribution is explicit for the latest run",
            "the first `Execution Reality` slice is coherent through Packet 10",
            "treat this as the first completed `Execution Reality` checkpoint",
        ]:
            if needle not in text:
                failures.append(f"doc_missing:{needle}")

    if not CURRENT_STATUS.exists():
        failures.append("missing_current_status_doc")
    else:
        text = CURRENT_STATUS.read_text(encoding="utf-8")
        for needle in [
            "Execution_reality_architect_status_update_2026-04-02.md",
            "## Current Execution Reality Checkpoint",
            "`Packet 01-10 defined and verified`",
        ]:
            if needle not in text:
                failures.append(f"current_status_missing:{needle}")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
