from __future__ import annotations

from ai_hedge_bot.analytics.analytics_service import AnalyticsService
from ai_hedge_bot.research_factory.service import ResearchFactoryService


def build() -> dict:
    analytics = AnalyticsService()
    signal = analytics.signal_summary()
    research = ResearchFactoryService().overview()
    governance = ResearchFactoryService().governance_overview()
    counts = research.get('counts', {})
    latest_model = research.get('latest_model') or {}
    latest_promotion = governance.get('latest_promotion') or {}
    latest_review = governance.get('latest_live_review') or {}
    latest_decay = governance.get('latest_decay') or {}
    return {
        'dashboard': 'research',
        'status': 'ok',
        'cards': {
            'signal_count': signal.get('signal_count', 0),
            'top_symbol': signal.get('top_symbol'),
            'top_alpha_family': signal.get('top_alpha_family'),
            'experiment_count': counts.get('experiments', 0),
            'dataset_count': counts.get('datasets', 0),
            'feature_count': counts.get('features', 0),
            'model_count': counts.get('models', 0),
            'latest_model_state': latest_model.get('state'),
            'latest_promotion_decision': latest_promotion.get('decision'),
            'latest_live_review_decision': latest_review.get('decision'),
            'latest_decay_severity': latest_decay.get('severity'),
        },
        'research_factory': {
            'counts': counts,
            'state_counts': research.get('state_counts', {}),
            'governance': research.get('governance', {}),
        },
    }
