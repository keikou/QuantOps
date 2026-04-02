from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "System_learning_resume_memo_2026-04-02.md"


def main() -> None:
    failures: list[str] = []

    if not DOC.exists():
        failures.append("missing_system_learning_resume_memo")
    else:
        text = DOC.read_text(encoding="utf-8")
        for needle in [
            "Research / Promotion Intelligence v1",
            "RPI-06",
            "System-Level Learning / Feedback Integration",
            "What To Tell Architect In A New Chat",
            "What To Tell Codex In A New Chat",
            "One-Day-Later Resume Flow",
        ]:
            if needle not in text:
                failures.append(f"doc_missing:{needle}")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
