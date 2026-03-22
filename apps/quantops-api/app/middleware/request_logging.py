from __future__ import annotations

import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.core.request_context import bind_request_context, reset_request_context

logger = logging.getLogger("uvicorn.error")
TARGET_PATHS = {
    "/api/v1/dashboard/overview",
    "/api/v1/portfolio/positions",
    "/api/v1/risk/snapshot",
    "/api/v1/monitoring/system",
}


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or request.headers.get("x-client-request-id") or f"api-{uuid.uuid4().hex[:8]}"
        start = time.perf_counter()
        request.state.request_id = request_id
        context_tokens = bind_request_context(request_id, request.url.path)

        try:
            response = await call_next(request)
        except Exception as exc:  # pragma: no cover - defensive logging path
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            reset_request_context(context_tokens)
            logger.exception(
                "request_failed method=%s path=%s request_id=%s duration_ms=%s error=%s",
                request.method,
                request.url.path,
                request_id,
                duration_ms,
                repr(exc),
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
                headers={"X-Request-Id": request_id},
            )

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-Id"] = request_id
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
        reset_request_context(context_tokens)
        return response
