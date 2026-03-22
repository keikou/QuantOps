from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.dependencies import get_v12_client

router = APIRouter(prefix="/api/v1/scheduler", tags=["scheduler"])


@router.post("/run-now")
def run_now(mode: str | None = Query(default=None), client=Depends(get_v12_client)):
    if mode:
        return client.run_with_mode(mode=mode)
    return {"ok": True, "message": "fallback to existing scheduler run-now path"}
