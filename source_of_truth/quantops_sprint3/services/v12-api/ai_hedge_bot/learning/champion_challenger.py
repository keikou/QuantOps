from __future__ import annotations

from typing import Any

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id


class ChampionChallenger:
    def __init__(self) -> None:
        self.store = CONTAINER.runtime_store

    def run(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        models = self._top_models(limit=2)
        if len(models) < 2:
            self._seed_shadow_candidate()
            models = self._top_models(limit=2)
        champion = models[0]
        challenger = models[1]
        champion_score = self._score(champion)
        challenger_score = self._score(challenger)
        winner = 'champion' if champion_score >= challenger_score else 'challenger'
        capital_shift = 0.0 if winner == 'champion' else 0.15
        row = {
            'run_id': f'cc_{new_cycle_id()}',
            'created_at': utc_now_iso(),
            'champion_model_id': champion['model_id'],
            'challenger_model_id': challenger['model_id'],
            'champion_score': champion_score,
            'challenger_score': challenger_score,
            'winner': winner,
            'recommended_action': 'switch_live' if winner == 'challenger' else 'keep_live',
            'capital_shift': capital_shift,
            'notes': payload.get('notes', 'phaseh sprint3 champion challenger'),
        }
        self.store.append('champion_challenger_runs', row)
        return row

    def list_latest(self, limit: int = 25) -> list[dict[str, Any]]:
        return self.store.fetchall_dict(
            """
            SELECT run_id, created_at, champion_model_id, challenger_model_id,
                   champion_score, challenger_score, winner, recommended_action,
                   capital_shift, notes
            FROM champion_challenger_runs
            ORDER BY created_at DESC
            LIMIT ?
            """,
            [limit],
        )

    def ensure_seed(self) -> None:
        count = self.store.fetchone_dict('SELECT COUNT(*) AS c FROM champion_challenger_runs')
        if int((count or {}).get('c') or 0) == 0:
            self.run({'notes': 'seed champion challenger'})

    def _top_models(self, limit: int) -> list[dict[str, Any]]:
        return self.store.fetchall_dict(
            """
            SELECT m.model_id, m.model_version, m.state, COALESCE(v.summary_score, 0.0) AS summary_score
            FROM model_registry m
            LEFT JOIN validation_registry v ON v.experiment_id = m.experiment_id
            ORDER BY summary_score DESC, m.created_at DESC
            LIMIT ?
            """,
            [limit],
        )

    def _score(self, row: dict[str, Any]) -> float:
        score = float(row.get('summary_score') or 0.0)
        if str(row.get('state')) == 'live':
            score += 0.02
        if str(row.get('state')) == 'approved':
            score += 0.01
        return round(score, 6)

    def _seed_shadow_candidate(self) -> None:
        latest = self.store.fetchone_dict('SELECT experiment_id, dataset_version, feature_version FROM model_registry ORDER BY created_at DESC LIMIT 1') or {}
        self.store.append('model_registry', {
            'model_id': f'model_{new_cycle_id()}',
            'created_at': utc_now_iso(),
            'experiment_id': latest.get('experiment_id', 'exp_seed'),
            'dataset_version': latest.get('dataset_version', 'dataset.synthetic.v1'),
            'feature_version': latest.get('feature_version', 'features.core.v1'),
            'model_version': 'model.challenger.v1',
            'validation_metrics_json': self.store.to_json({'summary_score': 0.83, 'max_drawdown': 0.07}),
            'state': 'shadow',
            'notes': 'auto-seeded challenger',
        })
