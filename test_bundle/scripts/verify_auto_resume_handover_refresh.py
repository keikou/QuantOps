from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = REPO_ROOT / "docs" / "Auto_resume_handover_2026-04-02.md"
MANIFEST_PLAN = REPO_ROOT / "docs" / "Hardening_handover_manifest_plan.md"


def verify() -> dict[str, object]:
    failures: list[str] = []

    if not DOC_PATH.exists():
        failures.append("auto resume handover 2026-04-02 doc does not exist")
        content = ""
    else:
        content = DOC_PATH.read_text(encoding="utf-8")

    if not MANIFEST_PLAN.exists():
        failures.append("hardening handover manifest plan doc does not exist")

    required_tokens = [
        "Auto Resume Handover 2026-04-02",
        "codex/post-phase7-hardening",
        "System Reliability Hardening Track",
        "/system/hardening-handover-manifest",
        "/system/hardening-evidence-snapshot/latest",
        "/system/hardening-architect-handoff/latest",
        "verify_hardening_status_surface.py",
        "verify_hardening_handover_manifest.py",
        "Do not reopen phase-closure work unless a real regression is found.",
    ]
    for token in required_tokens:
        if token not in content:
            failures.append(f"auto resume handover missing token: {token}")

    return {
        "status": "ok" if not failures else "failed",
        "lane": "auto_resume_handover_refresh",
        "doc_path": str(DOC_PATH),
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the refreshed auto-resume handover points at the current hardening entrypoints.")
    parser.add_argument("--json", action="store_true", help="Print JSON only")
    args = parser.parse_args()

    try:
        result = verify()
    except Exception as exc:
        print(f"Verification failed unexpectedly: {exc}", file=sys.stderr)
        return 3

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
