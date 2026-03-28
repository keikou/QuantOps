from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _is_frontend_timeout(row: dict[str, Any]) -> bool:
    if row.get("event_type") != "api_error":
        return False
    if str(row.get("status") or "").lower() == "timeout":
        return True
    details = row.get("details") or {}
    message = str(details.get("message") or "").lower()
    return "timeout" in message


def _is_backend_timeout(row: dict[str, Any]) -> bool:
    if row.get("timeout_detected") is True:
        return True
    status = row.get("status")
    return status in {408, 504}


def _sort_key(row: dict[str, Any]) -> tuple[str, str]:
    return str(row.get("timestamp") or row.get("server_received_at") or row.get("client_timestamp") or ""), str(row.get("event_type") or "")


def analyze(frontend_events: Path, quantops_requests: Path, v12_requests: Path) -> list[dict[str, Any]]:
    by_trace: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: {"frontend": [], "quantops": [], "v12": []})

    for row in _read_jsonl(frontend_events):
        trace_id = str(row.get("trace_id") or "")
        if trace_id:
            by_trace[trace_id]["frontend"].append(row)
    for row in _read_jsonl(quantops_requests):
        trace_id = str(row.get("trace_id") or "")
        if trace_id:
            by_trace[trace_id]["quantops"].append(row)
    for row in _read_jsonl(v12_requests):
        trace_id = str(row.get("trace_id") or "")
        if trace_id:
            by_trace[trace_id]["v12"].append(row)

    incidents: list[dict[str, Any]] = []
    for trace_id, groups in by_trace.items():
        frontend_timeouts = [row for row in groups["frontend"] if _is_frontend_timeout(row)]
        quantops_timeouts = [row for row in groups["quantops"] if _is_backend_timeout(row)]
        v12_timeouts = [row for row in groups["v12"] if _is_backend_timeout(row)]
        if not frontend_timeouts and not quantops_timeouts and not v12_timeouts:
            continue
        page_paths = sorted({str(row.get("page_path") or "") for rows in groups.values() for row in rows if row.get("page_path")})
        incidents.append(
            {
                "trace_id": trace_id,
                "page_paths": page_paths,
                "frontend_timeout_count": len(frontend_timeouts),
                "quantops_timeout_count": len(quantops_timeouts),
                "v12_timeout_count": len(v12_timeouts),
                "frontend_events": sorted(groups["frontend"], key=_sort_key),
                "quantops_events": sorted(groups["quantops"], key=_sort_key),
                "v12_events": sorted(groups["v12"], key=_sort_key),
            }
        )
    incidents.sort(key=lambda row: row["trace_id"])
    return incidents


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze correlated timeout incidents across frontend, QuantOps API, and V12 logs.")
    parser.add_argument("--frontend-events", type=Path, default=Path("apps/quantops-api/runtime/logs/frontend_events.jsonl"))
    parser.add_argument("--quantops-requests", type=Path, default=Path("apps/quantops-api/runtime/logs/quantops_requests.jsonl"))
    parser.add_argument("--v12-requests", type=Path, default=Path("apps/v12-api/runtime/logs/v12_requests.jsonl"))
    parser.add_argument("--json", action="store_true", help="Print full JSON incident output.")
    args = parser.parse_args()

    incidents = analyze(args.frontend_events, args.quantops_requests, args.v12_requests)
    if args.json:
        print(json.dumps(incidents, ensure_ascii=False, indent=2))
        return 0

    if not incidents:
        print("No correlated timeout incidents found.")
        return 0

    for incident in incidents:
        page_text = ", ".join(incident["page_paths"]) if incident["page_paths"] else "(unknown page)"
        print(
            f"trace_id={incident['trace_id']} page={page_text} "
            f"frontend={incident['frontend_timeout_count']} "
            f"quantops={incident['quantops_timeout_count']} "
            f"v12={incident['v12_timeout_count']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
