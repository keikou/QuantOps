from __future__ import annotations

from datetime import datetime, timezone


def align_timestamp(timestamp: str) -> str:
    raw = str(timestamp)
    if raw.endswith('Z'):
        raw = raw[:-1] + '+00:00'
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat()
