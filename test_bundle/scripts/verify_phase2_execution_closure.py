from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


def _request_json(base_url: str, path: str, method: str = "GET") -> dict[str, Any]:
    url = urllib.parse.urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    request = urllib.request.Request(url, method=method)
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def _expect(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def verify(base_url: str, mode: str) -> dict[str, Any]:
    failures: list[str] = []

    run_payload = _request_json(base_url, f"/runtime/run-once?mode={urllib.parse.quote(mode)}", method="POST")
    run_id = str(run_payload.get("run_id") or "")

    _expect(run_payload.get("status") == "ok", "runtime/run-once did not return status=ok", failures)
    _expect(bool(run_id), "runtime/run-once did not return run_id", failures)

    bridge = _request_json(base_url, f"/execution/bridge/by-run/{run_id}")
    planner = _request_json(base_url, f"/execution/plans/by-run/{run_id}")
    fills = _request_json(base_url, "/execution/fills")
    quality = _request_json(base_url, "/execution/quality/latest_summary")
    overview = _request_json(base_url, "/portfolio/overview")
    events = _request_json(base_url, f"/runtime/events/by-run/{run_id}?limit=200")

    run_fills = [row for row in fills.get("items", []) if str(row.get("run_id") or "") == run_id]
    event_types = {str(item.get("event_type") or "") for item in events.get("items", [])}

    _expect(bridge.get("status") == "ok", "execution bridge status is not ok", failures)
    _expect(bridge.get("run_id") == run_id, "execution bridge run_id does not match run-once run_id", failures)
    _expect(bool(bridge.get("event_chain_complete")), "execution bridge event_chain_complete is false", failures)
    _expect(int(bridge.get("planned_count", 0) or 0) >= 1, "execution bridge planned_count < 1", failures)
    _expect(int(bridge.get("submitted_count", 0) or 0) >= 1, "execution bridge submitted_count < 1", failures)
    _expect(int(bridge.get("filled_count", 0) or 0) >= 1, "execution bridge filled_count < 1", failures)

    _expect(planner.get("status") == "ok", "execution planner truth status is not ok", failures)
    _expect(len(planner.get("items", [])) >= 1, "execution planner returned no items", failures)

    _expect(len(run_fills) >= 1, "execution fills returned no fills for this run", failures)
    _expect(quality.get("status") == "ok", "execution quality summary status is not ok", failures)
    _expect(quality.get("run_id") == run_id, "execution quality summary run_id does not match run-once run_id", failures)
    _expect(int(quality.get("fill_count", 0) or 0) == len(run_fills), "execution quality fill_count does not match run fills", failures)
    _expect(int(quality.get("order_count", 0) or 0) >= int(quality.get("fill_count", 0) or 0), "execution quality order_count < fill_count", failures)

    _expect(overview.get("status") == "ok", "portfolio overview status is not ok", failures)
    _expect(float(overview.get("total_equity", 0.0) or 0.0) > 0.0, "portfolio overview total_equity is not positive", failures)
    _expect(len(overview.get("positions", [])) >= 1, "portfolio overview returned no positions after successful cycle", failures)

    required_events = {
        "cycle_started",
        "planner_generated",
        "order_submitted",
        "fill_recorded",
        "portfolio_updated",
        "cycle_completed",
    }
    _expect(required_events.issubset(event_types), "runtime events missing one or more required execution-loop event types", failures)

    return {
        "status": "ok" if not failures else "failed",
        "base_url": base_url,
        "mode": mode,
        "run_id": run_id,
        "bridge_state": bridge.get("bridge_state"),
        "planned_count": int(bridge.get("planned_count", 0) or 0),
        "submitted_count": int(bridge.get("submitted_count", 0) or 0),
        "filled_count": int(bridge.get("filled_count", 0) or 0),
        "run_fill_count": len(run_fills),
        "quality_order_count": int(quality.get("order_count", 0) or 0),
        "quality_fill_count": int(quality.get("fill_count", 0) or 0),
        "position_count": len(overview.get("positions", [])),
        "total_equity": float(overview.get("total_equity", 0.0) or 0.0),
        "event_types": sorted(event_types),
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Phase2 execution loop closure against a live V12 API.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Base URL for the V12 API")
    parser.add_argument("--mode", default="paper", help="runtime/run-once mode to execute")
    parser.add_argument("--json", action="store_true", help="Print JSON only")
    args = parser.parse_args()

    try:
        result = verify(args.base_url, args.mode)
    except urllib.error.URLError as exc:
        print(f"Failed to reach V12 API: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"Verification failed unexpectedly: {exc}", file=sys.stderr)
        return 3

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"status={result['status']} run_id={result['run_id']} bridge_state={result['bridge_state']}")
        print(
            "counts "
            f"planned={result['planned_count']} "
            f"submitted={result['submitted_count']} "
            f"filled={result['filled_count']} "
            f"positions={result['position_count']} "
            f"quality_orders={result['quality_order_count']} "
            f"quality_fills={result['quality_fill_count']}"
        )
        print(f"total_equity={result['total_equity']:.2f}")
        if result["failures"]:
            print("failures:")
            for failure in result["failures"]:
                print(f"- {failure}")

    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
