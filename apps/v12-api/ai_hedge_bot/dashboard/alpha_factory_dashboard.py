from __future__ import annotations

from ai_hedge_bot.autonomous_alpha.service import AutonomousAlphaService


def build() -> dict:
    service = AutonomousAlphaService()
    overview = service.overview()
    latest_ranking = overview.get('latest_ranking') or {}
    latest_eval = overview.get('latest_evaluation') or {}
    return {
        'dashboard': 'alpha_factory',
        'status': 'ok',
        'cards': {
            'registry_count': overview.get('counts', {}).get('registry', 0),
            'ranking_count': overview.get('counts', {}).get('rankings', 0),
            'evaluation_count': overview.get('counts', {}).get('evaluations', 0),
            'promotion_count': overview.get('counts', {}).get('promotions', 0),
            'top_alpha_id': latest_ranking.get('alpha_id'),
            'top_rank_score': latest_ranking.get('rank_score'),
            'latest_decision': latest_ranking.get('recommended_action') or latest_eval.get('decision'),
        },
        'overview': overview,
    }
