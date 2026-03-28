from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.request_context import bind_request_context, reset_request_context
from ai_hedge_bot.data.storage.jsonl_logger import JsonlLogger


logger = logging.getLogger("uvicorn.error")
request_jsonl_logger = JsonlLogger(CONTAINER.config.runtime_dir / "logs" / "v12_requests.jsonl")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or f"v12-{uuid.uuid4().hex[:8]}"
        trace_id = request.headers.get("x-trace-id") or request_id
        session_id = request.headers.get("x-session-id")
        page_path = request.headers.get("x-page-path")
        start = time.perf_counter()
        request.state.request_id = request_id
        request.state.trace_id = trace_id
        request.state.session_id = session_id
        request.state.page_path = page_path
        context_tokens = bind_request_context(
            request_id=request_id,
            trace_id=trace_id,
            session_id=session_id,
            page_path=page_path,
            request_path=request.url.path,
        )

        try:
            response = await call_next(request)
        except Exception as exc:  # pragma: no cover
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.exception(
                "v12_request_failed method=%s path=%s request_id=%s trace_id=%s session_id=%s page_path=%s duration_ms=%s error=%s",
                request.method,
                request.url.path,
                request_id,
                trace_id,
                session_id,
                page_path,
                duration_ms,
                repr(exc),
            )
            request_jsonl_logger.append(
                {
                    "timestamp": utc_now_iso(),
                    "service": "v12-api",
                    "event_type": "request_failed",
                    "method": request.method,
                    "path": request.url.path,
                    "status": 500,
                    "request_id": request_id,
                    "trace_id": trace_id,
                    "session_id": session_id,
                    "page_path": page_path,
                    "duration_ms": duration_ms,
                    "error": repr(exc),
                }
            )
            reset_request_context(context_tokens)
            return JSONResponse(
                {
                    "error": "Internal server error",
                    "request_id": request_id,
                    "trace_id": trace_id,
                },
                status_code=500,
                headers={"X-Request-Id": request_id, "X-Trace-Id": trace_id},
            )

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-Id"] = request_id
        response.headers["X-Trace-Id"] = trace_id
        logger.info(
            "v12_request_complete method=%s path=%s status=%s request_id=%s trace_id=%s session_id=%s page_path=%s duration_ms=%s",
            request.method,
            request.url.path,
            response.status_code,
            request_id,
            trace_id,
            session_id,
            page_path,
            duration_ms,
        )
        request_jsonl_logger.append(
            {
                "timestamp": utc_now_iso(),
                "service": "v12-api",
                "event_type": "request_complete",
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "request_id": request_id,
                "trace_id": trace_id,
                "session_id": session_id,
                "page_path": page_path,
                "duration_ms": duration_ms,
            }
        )
        reset_request_context(context_tokens)
        return response
