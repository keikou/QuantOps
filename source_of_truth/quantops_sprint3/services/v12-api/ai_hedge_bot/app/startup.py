from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from ai_hedge_bot.app.container import CONTAINER


def run_startup_checks() -> dict:
    runtime_dir = CONTAINER.config.runtime_dir
    runtime_dir.mkdir(parents=True, exist_ok=True)
    return {
        'runtime_dir': str(runtime_dir),
        'mode': CONTAINER.mode.value,
        'status': 'ok',
    }


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    run_startup_checks()
    yield
