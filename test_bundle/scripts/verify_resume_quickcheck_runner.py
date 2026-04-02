from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER = REPO_ROOT / "test_bundle" / "scripts" / "run_resume_quickcheck.py"


def verify() -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, str(RUNNER), "--json"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()
    if completed.returncode != 0:
        return {
            "status": "failed",
            "lane": "resume_quickcheck_runner",
            "failures": [f"runner failed: {stderr or stdout}"],
        }
    payload = json.loads(stdout)
    failures: list[str] = []
    if payload.get("status") != "ok":
        failures.append("quickcheck runner payload status should be ok")
    if int(payload.get("check_count", 0) or 0) != 2:
        failures.append("quickcheck runner check_count should be 2")
    if int(payload.get("passed_count", 0) or 0) != 2:
        failures.append("quickcheck runner passed_count should be 2")
    for item in payload.get("results") or []:
        if item.get("returncode") != 0:
            failures.append(f"quickcheck child failed: {item.get('script')}")
        if item.get("status") != "ok":
            failures.append(f"quickcheck child status not ok: {item.get('script')}")
    return {
        "status": "ok" if not failures else "failed",
        "lane": "resume_quickcheck_runner",
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the resume quickcheck runner executes the core resume verifiers.")
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
