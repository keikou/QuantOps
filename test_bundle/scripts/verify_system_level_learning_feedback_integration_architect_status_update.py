from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "System_level_learning_feedback_integration_architect_status_update_2026-04-02.md"


def main() -> None:
    failures: list[str] = []

    if not DOC.exists():
        failures.append("missing_sllfi_architect_status_update")
    else:
        text = DOC.read_text(encoding="utf-8")
        for needle in [
            "/system/learning-feedback/latest",
            "/system/learning-applied-consumption/latest",
            "Packet 01",
            "Packet 05",
            "first `applied-consumption checkpoint`",
        ]:
            if needle not in text:
                failures.append(f"doc_missing:{needle}")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
