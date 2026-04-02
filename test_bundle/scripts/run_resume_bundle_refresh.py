from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
V12_APP = REPO_ROOT / "apps" / "v12-api"
if str(V12_APP) not in sys.path:
    sys.path.insert(0, str(V12_APP))

from fastapi.testclient import TestClient  # noqa: E402

from ai_hedge_bot.app.main import app  # noqa: E402


client = TestClient(app)

STEPS = [
    ("hardening_evidence_snapshot", "POST", "/system/hardening-evidence-snapshot/save"),
    ("hardening_architect_handoff", "POST", "/system/hardening-architect-handoff/save"),
    ("resume_operator_packet", "POST", "/system/resume-operator-packet/save"),
]


def run_refresh() -> dict[str, object]:
    results: list[dict[str, object]] = []
    for name, method, path in STEPS:
        if method == "POST":
            response = client.post(path)
        else:
            response = client.get(path)
        payload = {}
        try:
            payload = response.json()
        except Exception:
            payload = {}
        results.append(
            {
                "step": name,
                "status_code": response.status_code,
                "status": payload.get("status"),
                "path": payload.get("path"),
            }
        )

    ok = all(item["status_code"] == 200 and item["status"] == "ok" for item in results)
    return {
        "status": "ok" if ok else "failed",
        "step_count": len(results),
        "refreshed_count": sum(1 for item in results if item["status_code"] == 200 and item["status"] == "ok"),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh the saved resume bundle artifacts.")
    parser.add_argument("--json", action="store_true", help="Print JSON only")
    args = parser.parse_args()

    result = run_refresh()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"status={result['status']} "
            f"refreshed={result['refreshed_count']} "
            f"total={result['step_count']}"
        )
        for item in result["results"]:
            print(f"{item['step']}: status_code={item['status_code']} status={item['status']} path={item['path']}")
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
