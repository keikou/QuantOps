from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
V12_APP = REPO_ROOT / "apps" / "v12-api"
if str(V12_APP) not in sys.path:
    sys.path.insert(0, str(V12_APP))

from fastapi.testclient import TestClient  # noqa: E402

from ai_hedge_bot.app.main import app  # noqa: E402


client = TestClient(app)


def build_resume_summary() -> dict[str, Any]:
    manifest_response = client.get("/system/hardening-handover-manifest")
    if manifest_response.status_code != 200:
        raise RuntimeError(
            f"/system/hardening-handover-manifest failed: {manifest_response.status_code} {manifest_response.text}"
        )
    manifest = manifest_response.json()

    snapshot_response = client.get("/system/hardening-evidence-snapshot/latest")
    if snapshot_response.status_code != 200:
        raise RuntimeError(
            f"/system/hardening-evidence-snapshot/latest failed: {snapshot_response.status_code} {snapshot_response.text}"
        )
    snapshot = snapshot_response.json()

    handoff_response = client.get("/system/hardening-architect-handoff/latest")
    if handoff_response.status_code != 200:
        raise RuntimeError(
            f"/system/hardening-architect-handoff/latest failed: {handoff_response.status_code} {handoff_response.text}"
        )
    handoff = handoff_response.json()

    status_artifact = (manifest.get("artifacts") or {}).get("hardening_status") or {}
    overall = status_artifact.get("overall") or {}
    docs = manifest.get("docs") or {}
    scripts = manifest.get("scripts") or {}

    return {
        "status": "ok",
        "track": manifest.get("track"),
        "branch_expectation": manifest.get("branch_expectation"),
        "latest_runtime_run_id": manifest.get("latest_runtime_run_id"),
        "overall_ready": manifest.get("overall_ready"),
        "ready_packet_count": overall.get("ready_packet_count"),
        "total_packet_count": overall.get("total_packet_count"),
        "manifest_consistency": manifest.get("consistency") or {},
        "resume_docs": {
            "auto_resume_handover": docs.get("auto_resume_handover"),
            "architect_handoff_latest": docs.get("architect_handoff_latest"),
            "hardening_status_update": docs.get("hardening_status_update"),
        },
        "resume_artifacts": {
            "snapshot_status": snapshot.get("status"),
            "snapshot_path": snapshot.get("path") or ((manifest.get("artifacts") or {}).get("evidence_snapshot") or {}).get("path"),
            "handoff_status": handoff.get("status"),
            "handoff_path": handoff.get("path") or ((manifest.get("artifacts") or {}).get("architect_handoff") or {}).get("path"),
        },
        "recommended_verifiers": scripts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Load the current hardening resume context from the handover manifest and related artifacts.")
    parser.add_argument("--json", action="store_true", help="Print JSON only")
    args = parser.parse_args()

    try:
        summary = build_resume_summary()
    except Exception as exc:
        print(f"Resume helper failed unexpectedly: {exc}", file=sys.stderr)
        return 3

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"status={summary['status']} track={summary['track']}")
        print(f"branch_expectation={summary.get('branch_expectation')}")
        print(f"latest_runtime_run_id={summary.get('latest_runtime_run_id')}")
        print(
            "packets "
            f"ready={summary.get('ready_packet_count')} "
            f"total={summary.get('total_packet_count')} "
            f"overall_ready={summary.get('overall_ready')}"
        )
        print(f"auto_resume_handover={summary['resume_docs'].get('auto_resume_handover')}")
        print(f"architect_handoff_latest={summary['resume_docs'].get('architect_handoff_latest')}")
        print(f"snapshot_path={summary['resume_artifacts'].get('snapshot_path')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
