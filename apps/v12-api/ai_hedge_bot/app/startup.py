from __future__ import annotations

import asyncio
import contextlib
import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.services.runtime.runtime_service import RuntimeService


async def _paper_runtime_loop(interval_sec: int) -> None:
    service = RuntimeService()
    while True:
        try:
            service.run_once(mode="paper", job_name="paper_runtime_loop", triggered_by="startup_loop")
        except Exception:
            pass
        await asyncio.sleep(max(interval_sec, 5))


def run_startup_checks() -> dict:
    runtime_dir = CONTAINER.config.runtime_dir
    runtime_dir.mkdir(parents=True, exist_ok=True)
    RuntimeService().seed_defaults()
    return {
        "runtime_dir": str(runtime_dir),
        "mode": CONTAINER.mode.value,
        "status": "ok",
    }


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    run_startup_checks()

    enable_startup_loop = os.getenv("ENABLE_STARTUP_PAPER_LOOP", "false").lower() == "true"
    interval_sec = int(os.getenv("PAPER_CYCLE_INTERVAL_SEC", "60"))

    background_task = None
    if enable_startup_loop:
        background_task = asyncio.create_task(_paper_runtime_loop(interval_sec))

    try:
        yield
    finally:
        if background_task is not None:
            background_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await background_task