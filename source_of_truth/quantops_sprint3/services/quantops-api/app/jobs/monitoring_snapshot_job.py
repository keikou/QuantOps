from __future__ import annotations

import asyncio

from app.core.deps import get_monitoring_service


def run_once() -> dict:
    return asyncio.run(get_monitoring_service().refresh())
