from __future__ import annotations

import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.deps import get_execution_service, get_monitoring_service, get_risk_service
from app.middleware.request_logging import RequestLoggingMiddleware
from app.core.config import get_settings
from app.db.init_db import init_db

GUI_FAST_PATH_WARMUP_DELAY_SECONDS = 3.0
GUI_FAST_PATH_WARMUP_MAX_WAIT_SECONDS = 15.0
GUI_FAST_PATH_WARMUP_POLL_SECONDS = 0.5
GUI_RISK_WARMUP_DELAY_SECONDS = 8.0
GUI_MONITORING_WARMUP_DELAY_SECONDS = 15.0
GUI_EXECUTION_WARMUP_DELAY_SECONDS = 24.0
GUI_FAST_PATH_WARMUP_READY_PATHS = (
    "/system/health",
    "/runtime/status",
    "/portfolio/overview-summary/latest",
)


def configure_runtime_logging() -> None:
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    for logger_name in ("uvicorn.error", "uvicorn.access"):
        runtime_logger = logging.getLogger(logger_name)
        for handler in runtime_logger.handlers:
            handler.setFormatter(formatter)


async def _warm_gui_fast_paths() -> None:
    try:
        await asyncio.sleep(GUI_FAST_PATH_WARMUP_DELAY_SECONDS)
        settings = get_settings()
        deadline = asyncio.get_running_loop().time() + GUI_FAST_PATH_WARMUP_MAX_WAIT_SECONDS
        async with httpx.AsyncClient(base_url=settings.v12_base_url.rstrip("/"), timeout=2.0) as client:
            while True:
                try:
                    ready = True
                    for path in GUI_FAST_PATH_WARMUP_READY_PATHS:
                        response = await client.get(path)
                        if response.status_code >= 500:
                            ready = False
                            break
                    if ready:
                        break
                except Exception:
                    pass
                if asyncio.get_running_loop().time() >= deadline:
                    break
                await asyncio.sleep(GUI_FAST_PATH_WARMUP_POLL_SECONDS)
        await asyncio.sleep(GUI_RISK_WARMUP_DELAY_SECONDS)
        await get_risk_service().refresh_snapshot(summary_only=True)
        await asyncio.sleep(max(0.0, GUI_MONITORING_WARMUP_DELAY_SECONDS - GUI_RISK_WARMUP_DELAY_SECONDS))
        await get_monitoring_service().refresh(summary_only=True)
        await asyncio.sleep(max(0.0, GUI_EXECUTION_WARMUP_DELAY_SECONDS - GUI_MONITORING_WARMUP_DELAY_SECONDS))
        execution_service = get_execution_service()
        await asyncio.gather(
            execution_service.get_planner_latest(),
            execution_service.get_state_latest(),
        )
    except Exception:
        logging.getLogger("uvicorn.error").exception("startup_warm_gui_fast_paths_failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_runtime_logging()
    init_db()
    warmup_task = asyncio.create_task(_warm_gui_fast_paths())
    yield
    if not warmup_task.done():
        warmup_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await warmup_task


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_allow_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
