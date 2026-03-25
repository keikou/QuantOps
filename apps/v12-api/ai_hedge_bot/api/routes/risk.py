from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter

from ai_hedge_bot.app.container import CONTAINER

router = APIRouter(prefix='/risk', tags=['risk'])
_risk_latest_cache: dict[str, object | None] = {"expires_at": None, "payload": None}
_RISK_LATEST_TTL_SECONDS = 3.0


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@router.get('/latest')
def risk_latest() -> dict:
    now = _utcnow()
    expires_at = _risk_latest_cache.get("expires_at")
    payload = _risk_latest_cache.get("payload")
    if isinstance(expires_at, datetime) and expires_at > now and isinstance(payload, dict):
        cached = dict(payload)
        cached["build_status"] = "fresh_cache"
        return cached
    live = dict(CONTAINER.sprint5c_service.get_latest_risk())
    live["build_status"] = "live"
    _risk_latest_cache["payload"] = dict(live)
    _risk_latest_cache["expires_at"] = now + timedelta(seconds=_RISK_LATEST_TTL_SECONDS)
    return live


@router.get('/history')
def risk_history(limit: int = 100) -> list[dict]:
    return CONTAINER.sprint5c_service.get_risk_history(limit=limit)
