from __future__ import annotations

import os
from fastapi import APIRouter, Depends

from app.services.governance_service import GovernanceService
from app.core.deps import get_v12_client, get_governance_repository
from app.clients.v12_client import V12Client
from app.repositories.governance_repository import GovernanceRepository

router = APIRouter(tags=['governance'])

@router.get('/overview')
def governance_overview():
    base_url = os.getenv('V12_BASE_URL', 'http://v12-api:8000')
    timeout_seconds = int(os.getenv('V12_TIMEOUT_SECONDS', '10'))
    service = GovernanceService(base_url=base_url, timeout_seconds=timeout_seconds)
    return service.get_overview()

@router.get('/budgets')
async def budgets(client: V12Client = Depends(get_v12_client)) -> dict:
    return await client.get_sprint5c_governance_budgets()

@router.get('/regime')
async def regime(client: V12Client = Depends(get_v12_client)) -> dict:
    return await client.get_sprint5c_governance_regime()


@router.get('/approvals')
def governance_approvals() -> dict:
    return {
        'status': 'ok',
        'items': [],
        'count': 0,
    }


@router.post('/refresh')
def governance_refresh(repository: GovernanceRepository = Depends(get_governance_repository)) -> dict:
    base_url = os.getenv('V12_BASE_URL', 'http://v12-api:8000')
    timeout_seconds = int(os.getenv('V12_TIMEOUT_SECONDS', '10'))
    service = GovernanceService(base_url=base_url, timeout_seconds=timeout_seconds)
    payload = service.get_overview()
    try:
        return repository.insert_snapshot(payload)
    except Exception:
        return payload
