from __future__ import annotations

import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.deps import get_monitoring_service, get_risk_service
from app.middleware.request_logging import RequestLoggingMiddleware
from app.core.config import get_settings
from app.db.init_db import init_db


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
        await asyncio.gather(
            get_monitoring_service().refresh(),
            get_risk_service().refresh_snapshot(),
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
