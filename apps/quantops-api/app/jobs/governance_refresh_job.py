from __future__ import annotations

import asyncio

from app.core.deps import get_governance_service


def run_once() -> dict:
    return asyncio.run(get_governance_service().refresh_overview())
