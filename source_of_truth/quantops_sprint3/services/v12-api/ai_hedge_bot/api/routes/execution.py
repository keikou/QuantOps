from __future__ import annotations

from fastapi import APIRouter
from ai_hedge_bot.app.container import CONTAINER

router = APIRouter(prefix='/execution', tags=['execution'])


@router.get('/quality/latest')
def execution_quality_latest() -> dict:
    if CONTAINER.latest_execution_quality:
        return CONTAINER.latest_execution_quality
    return {'status': 'ok', 'fill_rate': None, 'avg_slippage_bps': None, 'latency_ms_p50': None, 'latency_ms_p95': None}
