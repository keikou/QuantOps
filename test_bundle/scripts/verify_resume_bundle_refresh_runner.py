from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER = REPO_ROOT / "test_bundle" / "scripts" / "run_resume_bundle_refresh.py"
if str(RUNNER.parent) not in sys.path:
    sys.path.insert(0, str(RUNNER.parent))

from run_resume_bundle_refresh import run_refresh  # noqa: E402


def verify() -> dict[str, object]:
    payload = run_refresh()
    failures: list[str] = []
    if payload.get("status") != "ok":
        failures.append("refresh runner payload status should be ok")
    if int(payload.get("step_count", 0) or 0) != 3:
        failures.append("refresh runner step_count should be 3")
    if int(payload.get("refreshed_count", 0) or 0) != 3:
        failures.append("refresh runner refreshed_count should be 3")
    for item in payload.get("results") or []:
        if item.get("status_code") != 200:
            failures.append(f"refresh step failed: {item.get('step')}")
        if item.get("status") != "ok":
            failures.append(f"refresh step status not ok: {item.get('step')}")
        if not str(item.get("path") or ""):
            failures.append(f"refresh step missing path: {item.get('step')}")
    return {
        "status": "ok" if not failures else "failed",
        "lane": "resume_bundle_refresh_runner",
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the resume bundle refresh runner regenerates the saved artifacts.")
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
