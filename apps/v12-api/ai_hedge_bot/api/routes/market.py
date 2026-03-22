from __future__ import annotations

from fastapi import APIRouter
from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.data.quality.data_quality_engine import build_liveness_summary, build_quality_summary
from ai_hedge_bot.services.truth_engine import TruthEngine

router = APIRouter(prefix='/market', tags=['market'])
_truth = TruthEngine()


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


@router.get('/quote-config')
def quote_config() -> dict:
    return {'status': 'ok', 'config': _truth.price_runtime_config()}


@router.get('/quotes/live')
def live_quotes() -> dict:
    quotes = [quote.to_dict() for quote in _truth.quote_client.fetch_best_bid_ask_many(CONTAINER.config.symbols)]
    return {'status': 'ok', 'items': quotes, 'config': _truth.price_runtime_config()}
