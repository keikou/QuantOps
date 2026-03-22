from __future__ import annotations

from ai_hedge_bot.analytics.analytics_service import AnalyticsService


def build() -> dict:
    service = AnalyticsService()
    shadow = service.shadow_summary()
    quality = service.execution_quality()
    return {
        'dashboard': 'execution',
        'status': 'ok',
        'cards': {
            'shadow_order_count': shadow.get('shadow_order_count', 0),
            'shadow_fill_count': shadow.get('shadow_fill_count', 0),
            'fill_rate': quality.get('fill_rate'),
        },
    }
