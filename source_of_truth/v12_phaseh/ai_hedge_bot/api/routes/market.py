from __future__ import annotations

from fastapi import APIRouter
from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.data.quality.data_quality_engine import build_liveness_summary, build_quality_summary

router = APIRouter(prefix='/market', tags=['market'])


@router.get('/data-quality')
def data_quality() -> dict:
    return build_quality_summary(CONTAINER.config.symbols)


@router.get('/feed-liveness')
def feed_liveness() -> dict:
    return build_liveness_summary(CONTAINER.config.symbols)


@router.post('/collect/run')
def collect_run() -> dict:
    return CONTAINER.pipeline_service.collect(CONTAINER.config.symbols)


@router.post('/normalize/run')
def normalize_run() -> dict:
    if not CONTAINER.pipeline_service.latest_normalized() and not getattr(CONTAINER.pipeline_service, '_last_raw_batch', []):
        CONTAINER.pipeline_service.collect(CONTAINER.config.symbols)
    return CONTAINER.pipeline_service.normalize()
