from __future__ import annotations

import argparse
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = REPO_ROOT / "docs" / "Resume_bundle_completion_status_2026-04-02.md"


def verify() -> dict[str, object]:
    failures: list[str] = []
    if not DOC_PATH.exists():
        return {
            "status": "failed",
            "lane": "resume_bundle_completion_status",
            "failures": ["resume bundle completion status doc does not exist"],
        }

    content = DOC_PATH.read_text(encoding="utf-8")
    required_tokens = [
        "Resume Bundle Completion Status 2026-04-02",
        "resume_bundle_completed",
        "Auto_resume_handover_2026-04-02.md",
        "Resume_bundle_index_2026-04-02.md",
        "Resume_operator_packet_latest.md",
        "Hardening_architect_handoff_latest.md",
        "/system/hardening-handover-manifest",
        "run_resume_quickcheck.py --json",
        "run_resume_bundle_refresh.py --json",
        "resume_hardening_helper.py --json",
    ]
    for token in required_tokens:
        if token not in content:
            failures.append(f"resume bundle completion status missing token: {token}")

    return {
        "status": "ok" if not failures else "failed",
        "lane": "resume_bundle_completion_status",
        "doc_path": str(DOC_PATH),
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the resume bundle completion status doc summarizes the current resume stack.")
    parser.add_argument("--json", action="store_true", help="Print JSON only")
    args = parser.parse_args()
    result = verify()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"status={result['status']} lane={result['lane']}")
        print(f"doc_path={result.get('doc_path')}")
        if result["failures"]:
            print("failures:")
            for failure in result["failures"]:
                print(f"- {failure}")
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
