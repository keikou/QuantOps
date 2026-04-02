from __future__ import annotations

import argparse
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HANDOVER_DOC = REPO_ROOT / "docs" / "Auto_resume_handover_2026-04-02.md"
INDEX_DOC = REPO_ROOT / "docs" / "Resume_bundle_index_2026-04-02.md"


def verify() -> dict[str, object]:
    failures: list[str] = []
    handover = HANDOVER_DOC.read_text(encoding="utf-8") if HANDOVER_DOC.exists() else ""
    index_doc = INDEX_DOC.read_text(encoding="utf-8") if INDEX_DOC.exists() else ""

    required_tokens = [
        "run_resume_quickcheck.py --json",
        "run_resume_bundle_refresh.py --json",
        "resume_hardening_helper.py --json",
    ]
    for token in required_tokens:
        if token not in handover:
            failures.append(f"handover doc missing token: {token}")
        if token not in index_doc:
            failures.append(f"resume bundle index missing token: {token}")

    return {
        "status": "ok" if not failures else "failed",
        "lane": "resume_command_index_update",
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the resume command index is exposed in the main handover docs.")
    parser.add_argument("--json", action="store_true", help="Print JSON only")
    args = parser.parse_args()
    result = verify()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"status={result['status']} lane={result['lane']}")
        if result["failures"]:
            print("failures:")
            for failure in result["failures"]:
                print(f"- {failure}")
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
