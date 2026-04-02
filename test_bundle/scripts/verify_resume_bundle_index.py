from __future__ import annotations

import argparse
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX_DOC = REPO_ROOT / "docs" / "Resume_bundle_index_2026-04-02.md"


def verify() -> dict[str, object]:
    failures: list[str] = []
    if not INDEX_DOC.exists():
        return {
            "status": "failed",
            "lane": "resume_bundle_index",
            "doc_path": str(INDEX_DOC),
            "failures": ["resume bundle index doc does not exist"],
        }

    content = INDEX_DOC.read_text(encoding="utf-8")
    required_tokens = [
        "Resume Bundle Index 2026-04-02",
        "Auto_resume_handover_2026-04-02.md",
        "Resume_operator_packet_latest.md",
        "Hardening_architect_handoff_latest.md",
        "hardening_evidence_latest.json",
        "/system/hardening-handover-manifest",
        "/system/resume-operator-packet/latest",
        "verify_resume_operator_packet.py",
        "verify_resume_automation_helper.py",
    ]
    for token in required_tokens:
        if token not in content:
            failures.append(f"resume bundle index missing token: {token}")

    return {
        "status": "ok" if not failures else "failed",
        "lane": "resume_bundle_index",
        "doc_path": str(INDEX_DOC),
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the resume bundle index points to the current resume artifacts and surfaces.")
    parser.add_argument("--json", action="store_true", help="Print JSON only")
    args = parser.parse_args()

    result = verify()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"status={result['status']} lane={result['lane']}")
        print(f"doc_path={result['doc_path']}")
        if result["failures"]:
            print("failures:")
            for failure in result["failures"]:
                print(f"- {failure}")
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
