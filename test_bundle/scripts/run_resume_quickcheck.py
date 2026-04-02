from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "test_bundle" / "scripts"

CHECKS = [
    "verify_auto_resume_handover_refresh.py",
    "verify_resume_bundle_index.py",
]


def run_quickcheck() -> dict[str, object]:
    results: list[dict[str, object]] = []
    for name in CHECKS:
        script_path = SCRIPTS_DIR / name
        completed = subprocess.run(
            [sys.executable, str(script_path), "--json"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        stdout = (completed.stdout or "").strip()
        stderr = (completed.stderr or "").strip()
        parsed = None
        if stdout:
            try:
                parsed = json.loads(stdout)
            except Exception:
                parsed = None
        results.append(
            {
                "script": name,
                "returncode": completed.returncode,
                "status": None if parsed is None else parsed.get("status"),
                "stdout": stdout,
                "stderr": stderr,
            }
        )

    ok = all(item["returncode"] == 0 and item["status"] == "ok" for item in results)
    return {
        "status": "ok" if ok else "failed",
        "check_count": len(results),
        "passed_count": sum(1 for item in results if item["returncode"] == 0 and item["status"] == "ok"),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the core hardening resume quickchecks.")
    parser.add_argument("--json", action="store_true", help="Print JSON only")
    args = parser.parse_args()

    result = run_quickcheck()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"status={result['status']} "
            f"passed={result['passed_count']} "
            f"total={result['check_count']}"
        )
        for item in result["results"]:
            print(f"{item['script']}: returncode={item['returncode']} status={item['status']}")
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
