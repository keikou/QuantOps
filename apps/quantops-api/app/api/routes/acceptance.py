from __future__ import annotations

from fastapi import APIRouter, Depends
from app.core.deps import get_v12_client
from app.clients.v12_client import V12Client

router = APIRouter()

@router.get('/status')
async def status(client: V12Client = Depends(get_v12_client)) -> dict:
    return await client.get_acceptance_status()

@router.get('/checks')
async def checks(client: V12Client = Depends(get_v12_client)) -> dict:
    return await client.get_acceptance_checks()

@router.post('/run')
async def run_acceptance(client: V12Client = Depends(get_v12_client)) -> dict:
    return await client.run_acceptance()
