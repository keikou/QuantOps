from __future__ import annotations

from fastapi import APIRouter, Depends
from app.core.deps import get_v12_client
from app.clients.v12_client import V12Client

router = APIRouter()

@router.get('/current')
async def current_mode(client: V12Client = Depends(get_v12_client)) -> dict:
    return await client.get_current_mode()

@router.get('/config')
async def mode_config(client: V12Client = Depends(get_v12_client)) -> dict:
    return await client.get_mode_config()
