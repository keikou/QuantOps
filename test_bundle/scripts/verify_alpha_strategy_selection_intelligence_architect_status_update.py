from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "Alpha_strategy_selection_intelligence_architect_status_update_2026-04-02.md"


def main() -> None:
    failures: list[str] = []
    if not DOC.exists():
        failures.append("missing_architect_status_update_doc")
    else:
        text = DOC.read_text(encoding="utf-8")
        for needle in [
            "ASI-01",
            "ASI-05",
            "/alpha/intelligence/strategy-actions/latest",
            "effective selection slate",
            "switch to the next lane",
        ]:
            if needle not in text:
                failures.append(f"missing:{needle}")
    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
