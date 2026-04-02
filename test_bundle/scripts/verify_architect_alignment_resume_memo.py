from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
AUTO_RESUME = REPO_ROOT / "docs" / "Auto_resume_handover_2026-04-02.md"
ALIGNMENT_MEMO = REPO_ROOT / "docs" / "Architect_alignment_resume_memo_2026-04-02.md"


def main() -> None:
    failures: list[str] = []

    if not AUTO_RESUME.exists():
        failures.append("missing_auto_resume_handover")
    if not ALIGNMENT_MEMO.exists():
        failures.append("missing_architect_alignment_resume_memo")

    if AUTO_RESUME.exists():
        auto_text = AUTO_RESUME.read_text(encoding="utf-8")
        for required in [
            "Architect_alignment_resume_memo_2026-04-02.md",
            "current hardening slice is treated as sufficiently complete",
            "Execution Reality as the first candidate",
        ]:
            if required not in auto_text:
                failures.append(f"auto_resume_missing:{required}")

    if ALIGNMENT_MEMO.exists():
        memo_text = ALIGNMENT_MEMO.read_text(encoding="utf-8")
        for required in [
            "current hardening slice is sufficiently complete",
            "11 / 11",
            "Execution Reality",
            "What To Tell Architect In A New Chat",
            "What To Tell Codex In A New Thread",
        ]:
            if required not in memo_text:
                failures.append(f"alignment_memo_missing:{required}")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
