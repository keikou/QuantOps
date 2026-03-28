from __future__ import annotations

import asyncio
import importlib
import json
import os
from pathlib import Path

from fastapi.testclient import TestClient


def _clear_dep_caches() -> None:
    from app.core import deps as deps_module

    for name in (
        "get_v12_client",
        "get_dashboard_service",
        "get_portfolio_service",
        "get_analytics_service",
        "get_risk_service",
        "get_monitoring_service",
        "get_alert_service",
        "get_frontend_telemetry_service",
        "get_execution_service",
        "get_command_center_service",
    ):
        fn = getattr(deps_module, name, None)
        if fn is not None and hasattr(fn, "cache_clear"):
            fn.cache_clear()


def _build_quantops_client(tmp_path: Path) -> tuple[TestClient, Path]:
    os.environ["QUANTOPS_DB_PATH"] = str(tmp_path / "quantops.duckdb")
    os.environ["QUANTOPS_RUNTIME_DIR"] = str(tmp_path / "runtime")
    os.environ["V12_MOCK_MODE"] = "true"

    from app.core.config import get_settings
    from app.db.migrate import main as migrate_main

    get_settings.cache_clear()
    _clear_dep_caches()
    migrate_main()

    import app.middleware.request_logging as request_logging_module
    import app.main as app_main

    importlib.reload(request_logging_module)
    importlib.reload(app_main)
    return TestClient(app_main.create_app()), get_settings().log_dir


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_quantops_request_logging_persists_correlation_fields(tmp_path: Path) -> None:
    client, log_dir = _build_quantops_client(tmp_path)

    response = client.get(
        "/api/v1/health",
        headers={
            "X-Request-Id": "req-health-1",
            "X-Trace-Id": "trace-page-1",
            "X-Session-Id": "sess-1",
            "X-Page-Path": "/overview",
        },
    )

    assert response.status_code == 200
    assert response.headers["X-Request-Id"] == "req-health-1"
    assert response.headers["X-Trace-Id"] == "trace-page-1"

    request_log = log_dir / "quantops_requests.jsonl"
    rows = _read_jsonl(request_log)
    assert rows
    row = rows[-1]
    assert row["service"] == "quantops-api"
    assert row["event_type"] == "request_complete"
    assert row["path"] == "/api/v1/health"
    assert row["request_id"] == "req-health-1"
    assert row["trace_id"] == "trace-page-1"
    assert row["session_id"] == "sess-1"
    assert row["page_path"] == "/overview"
    assert row["timeout_detected"] is False


def test_frontend_events_route_persists_page_view_with_trace(tmp_path: Path) -> None:
    client, log_dir = _build_quantops_client(tmp_path)

    response = client.post(
        "/api/v1/admin/frontend-events",
        json={
            "event_type": "page_view",
            "trace_id": "trace-page-2",
            "request_id": "req-page-2",
            "session_id": "sess-2",
            "page_path": "/portfolio",
            "status": "ok",
            "details": {"user_agent": "pytest"},
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    event_log = log_dir / "frontend_events.jsonl"
    rows = _read_jsonl(event_log)
    assert rows
    row = rows[-1]
    assert row["event_type"] == "page_view"
    assert row["trace_id"] == "trace-page-2"
    assert row["request_id"] == "req-page-2"
    assert row["session_id"] == "sess-2"
    assert row["page_path"] == "/portfolio"
    assert row["details"]["user_agent"] == "pytest"


def test_v12_client_forwards_trace_headers(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class _DummyResponse:
        status_code = 200

        def __init__(self) -> None:
            self.request = object()

        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, str]:
            return {"status": "ok"}

    class _DummyAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            captured["client_kwargs"] = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def request(self, method: str, path: str, json=None, headers=None):
            captured["method"] = method
            captured["path"] = path
            captured["json"] = json
            captured["headers"] = headers or {}
            return _DummyResponse()

    async def _run() -> None:
        import httpx

        from app.clients.v12_client import V12Client
        from app.core.request_context import bind_request_context, reset_request_context

        original_client = httpx.AsyncClient
        monkeypatch.setattr(httpx, "AsyncClient", _DummyAsyncClient)
        tokens = bind_request_context(
            "req-upstream-1",
            "/api/v1/dashboard/overview",
            trace_id="trace-upstream-1",
            session_id="sess-upstream-1",
            page_path="/overview",
        )
        try:
            client = V12Client(base_url="http://127.0.0.1:8000", timeout=2.0, mock_mode=False)
            payload = await client.get_portfolio_dashboard()
            assert payload["status"] == "ok"
        finally:
            reset_request_context(tokens)
            monkeypatch.setattr(httpx, "AsyncClient", original_client)

    asyncio.run(_run())

    assert captured["method"] == "GET"
    assert captured["path"] == "/portfolio/overview-summary/latest"
    assert captured["headers"] == {
        "X-Request-Id": "req-upstream-1",
        "X-Trace-Id": "trace-upstream-1",
        "X-Session-Id": "sess-upstream-1",
        "X-Page-Path": "/overview",
    }


def test_v12_client_persists_upstream_timeout_log(tmp_path: Path, monkeypatch) -> None:
    captured: dict[str, object] = {}
    os.environ["QUANTOPS_DB_PATH"] = str(tmp_path / "quantops.duckdb")
    os.environ["QUANTOPS_RUNTIME_DIR"] = str(tmp_path / "runtime")
    os.environ["V12_MOCK_MODE"] = "true"

    from app.core.config import get_settings

    get_settings.cache_clear()
    _clear_dep_caches()

    import app.clients.v12_client as v12_client_module

    importlib.reload(v12_client_module)

    class _DummyAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            captured["client_kwargs"] = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def request(self, method: str, path: str, json=None, headers=None):
            raise TimeoutError("simulated timeout")

    async def _run() -> None:
        import httpx

        from app.core.request_context import bind_request_context, reset_request_context

        original_client = httpx.AsyncClient
        monkeypatch.setattr(httpx, "AsyncClient", _DummyAsyncClient)
        tokens = bind_request_context(
            "req-timeout-1",
            "/api/v1/dashboard/overview",
            trace_id="trace-timeout-1",
            session_id="sess-timeout-1",
            page_path="/overview",
        )
        try:
            client = v12_client_module.V12Client(base_url="http://127.0.0.1:8000", timeout=2.0, mock_mode=False)
            payload = await client.get_portfolio_dashboard()
            assert payload["status"] == "degraded"
        finally:
            reset_request_context(tokens)
            monkeypatch.setattr(httpx, "AsyncClient", original_client)

    asyncio.run(_run())

    rows = _read_jsonl(get_settings().log_dir / "quantops_upstream_v12.jsonl")
    assert rows
    row = rows[-1]
    assert row["event_type"] == "upstream_request_exception"
    assert row["trace_id"] == "trace-timeout-1"
    assert row["quantops_path"] == "/api/v1/dashboard/overview"
    assert row["upstream_path"] == "/dashboard/portfolio"
    assert row["timeout_detected"] is True
    assert row["timeout_source"] == "exception"
