from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "Portfolio_intelligence_architect_status_update_2026-04-02.md"
CURRENT_STATUS = REPO_ROOT / "docs" / "11_reports" / "current_status.md"


def main() -> None:
    failures: list[str] = []

    if not DOC.exists():
        failures.append("missing_portfolio_intelligence_architect_status_update_doc")
    else:
        text = DOC.read_text(encoding="utf-8")
        for needle in [
            "checkpoint_ready_for_architect_review",
            "Packet PI-05: previous resolved allocation actions are explicitly evaluated for realized portfolio effectiveness",
            "the first `Portfolio Intelligence` slice is coherent through Packet PI-05",
            "first completed `Portfolio Intelligence` outcome-evaluable checkpoint",
        ]:
            if needle not in text:
                failures.append(f"doc_missing:{needle}")

    if not CURRENT_STATUS.exists():
        failures.append("missing_current_status_doc")
    else:
        text = CURRENT_STATUS.read_text(encoding="utf-8")
        for needle in [
            "Portfolio_intelligence_architect_status_update_2026-04-02.md",
            "## Current Portfolio Intelligence Checkpoint",
            "`Packet PI-01-PI-05 defined and verified`",
        ]:
            if needle not in text:
                failures.append(f"current_status_missing:{needle}")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
