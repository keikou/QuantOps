from __future__ import annotations

from ai_hedge_bot.data.quality.freshness_checks import freshness_seconds


def build_quality_summary(symbols: list[str]) -> dict:
    return {
        'status': 'ok',
        'symbols': symbols,
        'warnings': [],
        'freshness_seconds': 0.0,
    }


def build_liveness_summary(symbols: list[str]) -> dict:
    return {
        'status': 'ok',
        'alive': symbols,
        'stale': [],
    }
