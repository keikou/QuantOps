from __future__ import annotations

from ai_hedge_bot.analytics.analytics_service import AnalyticsService


def build() -> dict:
    service = AnalyticsService()
    summary = service.portfolio_summary()
    latest = summary.get('latest', {})
    return {
        'dashboard': 'portfolio',
        'status': 'ok',
        'cards': {
            'portfolio_count': summary.get('portfolio_count', 0),
            'latest_kept_signals': latest.get('selected_count') or latest.get('kept_signals'),
            'gross_exposure_estimate': summary.get('gross_exposure_estimate', 0.0),
        },
    }
