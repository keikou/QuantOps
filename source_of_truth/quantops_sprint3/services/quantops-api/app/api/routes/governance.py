from __future__ import annotations

import os

from fastapi import APIRouter

from app.services.governance_service import GovernanceService

router = APIRouter(tags=["governance"])


@router.get("/overview")
def governance_overview():
    base_url = os.getenv("V12_BASE_URL", "http://v12-api:8000")
    timeout_seconds = int(os.getenv("V12_TIMEOUT_SECONDS", "10"))
    service = GovernanceService(base_url=base_url, timeout_seconds=timeout_seconds)
    return service.get_overview()
