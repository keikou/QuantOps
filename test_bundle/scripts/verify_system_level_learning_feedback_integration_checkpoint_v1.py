from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "System_level_learning_feedback_integration_checkpoint_v1.md"


def main() -> None:
    failures: list[str] = []

    if not DOC.exists():
        failures.append("missing_sllfi_checkpoint_v1")
    else:
        text = DOC.read_text(encoding="utf-8")
        for needle in [
            "SLLFI-05",
            "checkpoint_complete",
            "GET /system/learning-applied-consumption/latest",
            "Why This Counts As A Checkpoint",
            "Verification Basis",
        ]:
            if needle not in text:
                failures.append(f"doc_missing:{needle}")

    result = {"status": "ok" if not failures else "fail", "failures": failures}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
