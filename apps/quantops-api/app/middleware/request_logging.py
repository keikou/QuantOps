from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.core.jsonl_logger import JsonlLogger
from app.core.request_context import bind_request_context, reset_request_context

logger = logging.getLogger("uvicorn.error")
TARGET_PATHS = {
    "/api/v1/dashboard/overview",
    "/api/v1/portfolio/positions",
    "/api/v1/risk/snapshot",
    "/api/v1/monitoring/system",
}
request_jsonl_logger = JsonlLogger(get_settings().log_dir / "quantops_requests.jsonl")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_timeout_exception(exc: Exception) -> bool:
    name = type(exc).__name__.lower()
    text = repr(exc).lower()
    return "timeout" in name or "timeout" in text or "readtimeout" in text


def _is_timeout_status(status_code: int | None) -> bool:
    return status_code in {408, 504}


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or request.headers.get("x-client-request-id") or f"api-{uuid.uuid4().hex[:8]}"
        trace_id = request.headers.get("x-trace-id") or request_id
        session_id = request.headers.get("x-session-id")
        page_path = request.headers.get("x-page-path")
        start = time.perf_counter()
        request.state.request_id = request_id
        request.state.trace_id = trace_id
        request.state.session_id = session_id
        request.state.page_path = page_path
        context_tokens = bind_request_context(request_id, request.url.path, trace_id=trace_id, session_id=session_id, page_path=page_path)

        try:
            response = await call_next(request)
        except Exception as exc:  # pragma: no cover - defensive logging path
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            timeout_detected = _is_timeout_exception(exc)
            reset_request_context(context_tokens)
            logger.exception(
                "request_failed method=%s path=%s request_id=%s duration_ms=%s error=%s",
                request.method,
                request.url.path,
                request_id,
                duration_ms,
                repr(exc),
            )
            request_jsonl_logger.append(
                {
                    "timestamp": utc_now_iso(),
                    "service": "quantops-api",
                    "event_type": "request_failed",
                    "method": request.method,
                    "path": request.url.path,
                    "status": 500,
                    "request_id": request_id,
                    "trace_id": trace_id,
                    "session_id": session_id,
                    "page_path": page_path,
                    "duration_ms": duration_ms,
                    "timeout_detected": timeout_detected,
                    "timeout_source": "exception" if timeout_detected else None,
                    "error": repr(exc),
                }
            )
            return JSONResponse(
                {
                    "error": "Internal server error",
                    "detail": repr(exc),
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                    "duration_ms": duration_ms,
                },
                status_code=500,
                headers={"X-Request-Id": request_id, "X-Trace-Id": trace_id},
            )

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        timeout_detected = _is_timeout_status(response.status_code)
        response.headers["X-Request-Id"] = request_id
        response.headers["X-Trace-Id"] = trace_id
        handler_duration_ms = getattr(request.state, "handler_duration_ms", None)
        if handler_duration_ms is not None:
            serialization_duration_ms = round(max(duration_ms - float(handler_duration_ms), 0.0), 2)
            response.headers["X-QuantOps-Handler-Duration-Ms"] = str(round(float(handler_duration_ms), 2))
            response.headers["X-QuantOps-Serialization-Duration-Ms"] = str(serialization_duration_ms)
            response.headers["X-QuantOps-Total-Duration-Ms"] = str(duration_ms)
        log_fn = logger.warning if request.url.path in TARGET_PATHS else logger.info
        log_fn(
            "request_complete method=%s path=%s status=%s request_id=%s duration_ms=%s handler_duration_ms=%s serialization_duration_ms=%s",
            request.method,
            request.url.path,
            response.status_code,
            request_id,
            duration_ms,
            round(float(handler_duration_ms), 2) if handler_duration_ms is not None else None,
            round(max(duration_ms - float(handler_duration_ms), 0.0), 2) if handler_duration_ms is not None else None,
        )
        request_jsonl_logger.append(
            {
                "timestamp": utc_now_iso(),
                "service": "quantops-api",
                "event_type": "request_complete",
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "request_id": request_id,
                "trace_id": trace_id,
                "session_id": session_id,
                "page_path": page_path,
                "duration_ms": duration_ms,
                "timeout_detected": timeout_detected,
                "timeout_source": "status_code" if timeout_detected else None,
                "handler_duration_ms": round(float(handler_duration_ms), 2) if handler_duration_ms is not None else None,
                "serialization_duration_ms": round(max(duration_ms - float(handler_duration_ms), 0.0), 2) if handler_duration_ms is not None else None,
            }
        )
        reset_request_context(context_tokens)
        return response
