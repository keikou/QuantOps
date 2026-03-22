from __future__ import annotations

from fastapi import APIRouter, Depends

from app.clients.v12_client import V12Client
from app.core.deps import get_v12_client

router = APIRouter()


@router.get('/registry')
async def registry(client: V12Client = Depends(get_v12_client)) -> dict:
    data = await client.get_strategy_registry()
    if isinstance(data, dict) and data.get('status') == 'missing':
        return {
            'status': 'ok',
            'enabled_count': 0,
            'strategies': [],
            'as_of': None,
        }
    return data


@router.get('/risk-budget')
async def risk_budget(client: V12Client = Depends(get_v12_client)) -> dict:
    data = await client.get_strategy_risk_budget()
    if isinstance(data, dict) and data.get('status') == 'missing':
        return {
            'status': 'ok',
            'risk': {'gross_exposure': 0.0, 'net_exposure': 0.0, 'per_strategy': []},
            'global': {'status': 'ok', 'alerts': []},
            'as_of': None,
        }
    return data
