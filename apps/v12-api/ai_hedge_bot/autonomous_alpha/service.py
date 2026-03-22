from __future__ import annotations

import json
from typing import Any

from ai_hedge_bot.alpha.alpha_registry import ALPHA_REGISTRY
from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id
from ai_hedge_bot.research_factory.service import ResearchFactoryService


class AutonomousAlphaService:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store
        self.research = ResearchFactoryService()
        self._ensure_seed_data()

    def _ensure_seed_data(self) -> None:
        existing = self.store.fetchone_dict('SELECT COUNT(*) AS c FROM alpha_registry') or {'c': 0}
        if int(existing.get('c') or 0) > 0:
            return
        created_at = utc_now_iso()
        rows: list[dict[str, Any]] = []
        status_rows: list[dict[str, Any]] = []
        ranking_rows: list[dict[str, Any]] = []
        library_rows: list[dict[str, Any]] = []
        eval_rows: list[dict[str, Any]] = []
        promotion_rows: list[dict[str, Any]] = []
        for idx, meta in enumerate(list(ALPHA_REGISTRY.values())[:6]):
            alpha_id = meta.alpha_name
            row = {
                'alpha_id': alpha_id,
                'created_at': created_at,
                'alpha_family': meta.alpha_family,
                'factor_type': meta.factor_type,
                'horizon': meta.primary_horizon,
                'turnover_profile': meta.turnover_profile,
                'feature_dependencies_json': self.store.to_json(meta.required_features),
                'risk_profile': 'balanced' if idx % 2 == 0 else 'aggressive',
                'execution_sensitivity': round(0.22 + idx * 0.05, 6),
                'state': 'validated' if idx < 2 else 'candidate',
                'source': 'seed',
                'notes': 'seeded from existing alpha registry',
            }
            rows.append(row)
            status_rows.append({
                'event_id': new_cycle_id(),
                'created_at': created_at,
                'alpha_id': alpha_id,
                'event_type': 'seed',
                'from_state': 'new',
                'to_state': row['state'],
                'reason': 'phaseh sprint4 bootstrap',
            })
            score = round(0.72 + max(0, 4 - idx) * 0.025 - row['execution_sensitivity'] * 0.08, 6)
            ranking_rows.append({
                'ranking_id': new_cycle_id(),
                'created_at': created_at,
                'alpha_id': alpha_id,
                'rank_score': score,
                'expected_return': round(0.05 + score * 0.08, 6),
                'risk_adjusted_score': round(score * 0.92, 6),
                'execution_cost_adjusted_score': round(score - row['execution_sensitivity'] * 0.05, 6),
                'diversification_value': round(0.48 + idx * 0.03, 6),
                'recommended_action': 'promote' if idx == 0 else ('shadow' if idx < 3 else 'research'),
            })
            library_rows.append({
                'library_id': new_cycle_id(),
                'created_at': created_at,
                'alpha_id': alpha_id,
                'alpha_family': meta.alpha_family,
                'factor_type': meta.factor_type,
                'state': row['state'],
                'rank_score': score,
                'usage_count': max(1, 6 - idx),
                'tags_json': self.store.to_json([meta.alpha_family, meta.factor_type, meta.turnover_profile]),
            })
        top_alpha = rows[0]['alpha_id']
        eval_rows.append({
            'evaluation_id': new_cycle_id(),
            'created_at': created_at,
            'alpha_id': top_alpha,
            'test_name': 'seed_validation',
            'summary_score': 0.83,
            'sharpe': 1.42,
            'max_drawdown': 0.09,
            'turnover': 0.31,
            'slippage_bps': 5.8,
            'fill_probability': 0.91,
            'decision': 'promote',
            'notes': 'seed baseline for sprint4',
        })
        promotion_rows.append({
            'promotion_id': new_cycle_id(),
            'created_at': created_at,
            'alpha_id': top_alpha,
            'decision': 'promote',
            'source_run_id': 'seed_run',
            'notes': 'seeded promotion recommendation',
        })
        self.store.append('alpha_registry', rows)
        self.store.append('alpha_status_events', status_rows)
        self.store.append('alpha_rankings', ranking_rows)
        self.store.append('alpha_library', library_rows)
        self.store.append('alpha_eval_results', eval_rows)
        self.store.append('alpha_promotions', promotion_rows)

    def _lookup_alpha(self, alpha_id: str) -> dict[str, Any] | None:
        return self.store.fetchone_dict(
            'SELECT * FROM alpha_registry WHERE alpha_id=? ORDER BY created_at DESC LIMIT 1',
            [alpha_id],
        )

    def overview(self) -> dict[str, Any]:
        registry_count = self.store.fetchone_dict('SELECT COUNT(*) AS c FROM alpha_registry') or {'c': 0}
        rank_count = self.store.fetchone_dict('SELECT COUNT(*) AS c FROM alpha_rankings') or {'c': 0}
        eval_count = self.store.fetchone_dict('SELECT COUNT(*) AS c FROM alpha_eval_results') or {'c': 0}
        promotion_count = self.store.fetchone_dict('SELECT COUNT(*) AS c FROM alpha_promotions') or {'c': 0}
        latest_rank = self.store.fetchone_dict('SELECT * FROM alpha_rankings ORDER BY created_at DESC, rank_score DESC LIMIT 1')
        latest_eval = self.store.fetchone_dict('SELECT * FROM alpha_eval_results ORDER BY created_at DESC LIMIT 1')
        library = self.library(limit=5)
        governance = self.research.governance_overview()
        return {
            'status': 'ok',
            'counts': {
                'registry': int(registry_count.get('c') or 0),
                'rankings': int(rank_count.get('c') or 0),
                'evaluations': int(eval_count.get('c') or 0),
                'promotions': int(promotion_count.get('c') or 0),
            },
            'latest_ranking': latest_rank,
            'latest_evaluation': latest_eval,
            'library': library,
            'governance_bridge': {
                'latest_promotion': governance.get('latest_promotion'),
                'latest_decay': governance.get('latest_decay'),
            },
        }

    def register(self, payload: dict[str, Any]) -> dict[str, Any]:
        created_at = utc_now_iso()
        alpha_id = str(payload.get('alpha_id') or f'alpha_{new_cycle_id()}')
        row = {
            'alpha_id': alpha_id,
            'created_at': created_at,
            'alpha_family': str(payload.get('alpha_family') or 'custom'),
            'factor_type': str(payload.get('factor_type') or 'hybrid'),
            'horizon': str(payload.get('horizon') or 'short'),
            'turnover_profile': str(payload.get('turnover_profile') or 'medium'),
            'feature_dependencies_json': self.store.to_json(payload.get('feature_dependencies', [])),
            'risk_profile': str(payload.get('risk_profile') or 'balanced'),
            'execution_sensitivity': float(payload.get('execution_sensitivity', 0.28)),
            'state': str(payload.get('state') or 'candidate'),
            'source': str(payload.get('source') or 'manual'),
            'notes': str(payload.get('notes') or 'manual alpha registration'),
        }
        self.store.append('alpha_registry', row)
        self.store.append('alpha_library', {
            'library_id': new_cycle_id(),
            'created_at': created_at,
            'alpha_id': alpha_id,
            'alpha_family': row['alpha_family'],
            'factor_type': row['factor_type'],
            'state': row['state'],
            'rank_score': float(payload.get('rank_score', 0.0)),
            'usage_count': int(payload.get('usage_count', 0)),
            'tags_json': self.store.to_json(payload.get('tags', [row['alpha_family'], row['factor_type']])),
        })
        self.store.append('alpha_status_events', {
            'event_id': new_cycle_id(),
            'created_at': created_at,
            'alpha_id': alpha_id,
            'event_type': 'register',
            'from_state': 'new',
            'to_state': row['state'],
            'reason': row['notes'],
        })
        return row

    def generate(self, payload: dict[str, Any]) -> dict[str, Any]:
        family = str(payload.get('alpha_family') or payload.get('theme') or 'momentum')
        factor_type = str(payload.get('factor_type') or ('carry' if family == 'derivatives' else family[:12]))
        horizon = str(payload.get('horizon') or 'short')
        feature_dependencies = payload.get('feature_dependencies') or ['momentum_4', 'volume_zscore']
        alpha_id = str(payload.get('alpha_id') or f'alpha.generated.{family}.{new_cycle_id()[-6:]}')
        row = self.register({
            'alpha_id': alpha_id,
            'alpha_family': family,
            'factor_type': factor_type,
            'horizon': horizon,
            'turnover_profile': payload.get('turnover_profile', 'medium'),
            'feature_dependencies': feature_dependencies,
            'risk_profile': payload.get('risk_profile', 'balanced'),
            'execution_sensitivity': payload.get('execution_sensitivity', 0.26),
            'state': 'generated',
            'source': 'alpha_generate',
            'notes': payload.get('notes', 'generated by autonomous alpha factory'),
            'tags': payload.get('tags', [family, factor_type, horizon]),
        })
        exp = {
            'experiment_id': new_cycle_id(),
            'created_at': utc_now_iso(),
            'alpha_id': alpha_id,
            'generation_theme': family,
            'design_json': self.store.to_json({
                'factor_type': factor_type,
                'features': feature_dependencies,
                'hypothesis': payload.get('hypothesis', f'{family} alpha generated from sprint4 factory'),
            }),
            'status': 'generated',
            'notes': 'initial design recorded by alpha factory',
        }
        self.store.append('alpha_experiments', exp)
        return {'alpha': row, 'experiment': exp}

    def test(self, payload: dict[str, Any]) -> dict[str, Any]:
        alpha_id = str(payload.get('alpha_id') or '')
        alpha = self._lookup_alpha(alpha_id)
        if alpha is None:
            generated = self.generate(payload)
            alpha = generated['alpha']
            alpha_id = alpha['alpha_id']
        score_hint = float(payload.get('signal_strength', 0.78))
        sharpe = round(0.75 + score_hint * 0.9, 6)
        max_drawdown = round(max(0.03, 0.16 - score_hint * 0.08), 6)
        turnover = round(0.18 + float(alpha.get('execution_sensitivity', 0.28)) * 0.4, 6)
        slippage = round(4.5 + float(alpha.get('execution_sensitivity', 0.28)) * 12.0, 6)
        fill_probability = round(max(0.62, 0.96 - float(alpha.get('execution_sensitivity', 0.28)) * 0.22), 6)
        summary_score = round(0.42 * sharpe + 0.35 * fill_probability + 0.25 * score_hint - 0.5 * max_drawdown - slippage / 150.0, 6)
        decision = 'pass' if summary_score >= 0.82 else ('shadow' if summary_score >= 0.68 else 'research')
        created_at = utc_now_iso()
        result = {
            'evaluation_id': new_cycle_id(),
            'created_at': created_at,
            'alpha_id': alpha_id,
            'test_name': str(payload.get('test_name') or 'phaseh_sprint4_backtest'),
            'summary_score': summary_score,
            'sharpe': sharpe,
            'max_drawdown': max_drawdown,
            'turnover': turnover,
            'slippage_bps': slippage,
            'fill_probability': fill_probability,
            'decision': decision,
            'notes': 'execution-aware alpha evaluation',
        }
        self.store.append('alpha_eval_results', result)
        self.store.append('alpha_experiments', {
            'experiment_id': new_cycle_id(),
            'created_at': created_at,
            'alpha_id': alpha_id,
            'generation_theme': alpha.get('alpha_family', 'custom'),
            'design_json': self.store.to_json({'test_name': result['test_name'], 'execution_sensitivity': alpha.get('execution_sensitivity')}),
            'status': 'tested',
            'notes': 'test completed by alpha factory',
        })
        self.store.append('alpha_status_events', {
            'event_id': new_cycle_id(),
            'created_at': created_at,
            'alpha_id': alpha_id,
            'event_type': 'test',
            'from_state': alpha.get('state', 'generated'),
            'to_state': decision,
            'reason': f'summary_score={summary_score}',
        })
        return result

    def evaluate(self, payload: dict[str, Any]) -> dict[str, Any]:
        alpha_id = str(payload.get('alpha_id') or '')
        latest = self.store.fetchone_dict('SELECT * FROM alpha_eval_results WHERE alpha_id=? ORDER BY created_at DESC LIMIT 1', [alpha_id]) if alpha_id else None
        if latest is None:
            latest = self.test(payload)
            alpha_id = latest['alpha_id']
        alpha = self._lookup_alpha(alpha_id) or {}
        summary_score = float(latest.get('summary_score', 0.0))
        execution_cost_adjusted = round(summary_score - float(latest.get('slippage_bps', 0.0)) / 200.0, 6)
        risk_adjusted = round(summary_score - float(latest.get('max_drawdown', 0.0)) * 0.6, 6)
        diversification_value = round(0.45 + len(str(alpha.get('alpha_family', 'x'))) * 0.01, 6)
        rank_score = round(0.52 * risk_adjusted + 0.34 * execution_cost_adjusted + 0.14 * diversification_value, 6)
        action = 'promote' if rank_score >= 0.8 else ('shadow' if rank_score >= 0.68 else 'research')
        created_at = utc_now_iso()
        ranking = {
            'ranking_id': new_cycle_id(),
            'created_at': created_at,
            'alpha_id': alpha_id,
            'rank_score': rank_score,
            'expected_return': round(float(latest.get('sharpe', 0.0)) * 0.08, 6),
            'risk_adjusted_score': risk_adjusted,
            'execution_cost_adjusted_score': execution_cost_adjusted,
            'diversification_value': diversification_value,
            'recommended_action': action,
        }
        self.store.append('alpha_rankings', ranking)
        if action == 'promote':
            self.store.append('alpha_promotions', {
                'promotion_id': new_cycle_id(),
                'created_at': created_at,
                'alpha_id': alpha_id,
                'decision': 'promote',
                'source_run_id': ranking['ranking_id'],
                'notes': 'promoted by sprint4 ranker',
            })
        elif action == 'research':
            self.store.append('alpha_demotions', {
                'demotion_id': new_cycle_id(),
                'created_at': created_at,
                'alpha_id': alpha_id,
                'decision': 'research',
                'source_run_id': ranking['ranking_id'],
                'notes': 'returned to research queue by sprint4 ranker',
            })
        return ranking

    def ranking(self, limit: int = 20) -> list[dict[str, Any]]:
        return self.store.fetchall_dict(
            f'SELECT * FROM alpha_rankings ORDER BY rank_score DESC, created_at DESC LIMIT {int(limit)}'
        )

    def library(self, limit: int = 50) -> list[dict[str, Any]]:
        rows = self.store.fetchall_dict(
            f'SELECT * FROM alpha_library ORDER BY rank_score DESC, created_at DESC LIMIT {int(limit)}'
        )
        for row in rows:
            tags_json = row.pop('tags_json', '[]')
            try:
                row['tags'] = json.loads(tags_json)
            except Exception:
                row['tags'] = []
        return rows
