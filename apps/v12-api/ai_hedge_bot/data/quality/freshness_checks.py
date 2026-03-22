from __future__ import annotations

from datetime import datetime, timezone


def freshness_seconds(ts: str) -> float:
    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
    return max((datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds(), 0.0)
