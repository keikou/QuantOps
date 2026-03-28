from __future__ import annotations

from datetime import datetime, timezone

from app.core.config import get_settings
from app.core.jsonl_logger import JsonlLogger


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class FrontendTelemetryService:
    def __init__(self) -> None:
        settings = get_settings()
        self._logger = JsonlLogger(settings.log_dir / "frontend_events.jsonl")

    def record_event(self, payload: dict) -> dict:
        row = {
            "server_received_at": utc_now_iso(),
            "event_type": str(payload.get("event_type") or "unknown"),
            "trace_id": str(payload.get("trace_id") or "") or None,
            "request_id": str(payload.get("request_id") or "") or None,
            "session_id": str(payload.get("session_id") or "") or None,
            "page_path": str(payload.get("page_path") or "") or None,
            "user": str(payload.get("user") or "") or None,
            "role": str(payload.get("role") or "") or None,
            "status": str(payload.get("status") or "") or None,
            "action": str(payload.get("action") or "") or None,
            "target": str(payload.get("target") or "") or None,
            "client_timestamp": payload.get("timestamp"),
            "details": payload.get("details") if isinstance(payload.get("details"), dict) else {},
        }
        self._logger.append(row)
        return {"status": "ok", "recorded_at": row["server_received_at"]}
