from __future__ import annotations

from fastapi import APIRouter
from ai_hedge_bot.app.container import CONTAINER

router = APIRouter(tags=['system'])


def _payload() -> dict:
    return {
        'status': 'ok',
        'mode': CONTAINER.mode.value,
        'symbols': CONTAINER.config.symbols,
        'phase': 'H',
        'sprint': 4,
    }

@router.get('/system/health')
def system_health() -> dict:
    return _payload()

@router.get('/health')
def legacy_health() -> dict:
    return _payload()
