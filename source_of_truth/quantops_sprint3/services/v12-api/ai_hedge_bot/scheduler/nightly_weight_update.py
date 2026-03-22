from __future__ import annotations

from pathlib import Path
import json
import pandas as pd

from ai_hedge_bot.core.settings import SETTINGS
from ai_hedge_bot.core.utils import utc_now
from ai_hedge_bot.data.storage.jsonl_logger import JsonlLogger
from ai_hedge_bot.analytics.analytics_service import AnalyticsSyncService
from ai_hedge_bot.learning.alpha_learning import AlphaWeightStore
from ai_hedge_bot.learning.alpha_scorer import score_alpha


def run() -> dict:
    log_dir = SETTINGS.log_dir
    perf_path = log_dir / 'alpha_performance_summary.jsonl'
    weight_store = AlphaWeightStore(SETTINGS.weights_path)
    logger = JsonlLogger(log_dir / 'weight_updates.jsonl')
    analytics = AnalyticsSyncService(SETTINGS.db_path, log_dir)

    if not perf_path.exists():
        current = weight_store.load()
        logger.append({'event': 'weights', 'weights': current, 'alpha_scores': {}, 'timestamp': utc_now(), 'update_applied': False, 'reason': 'no_alpha_performance'})
        analytics.rebuild()
        return {'weights': current, 'update_applied': False}

    rows = [json.loads(line) for line in perf_path.read_text(encoding='utf-8').splitlines() if line.strip()]
    if not rows:
        current = weight_store.load()
        logger.append({'event': 'weights', 'weights': current, 'alpha_scores': {}, 'timestamp': utc_now(), 'update_applied': False, 'reason': 'empty_alpha_performance'})
        analytics.rebuild()
        return {'weights': current, 'update_applied': False}

    df = pd.json_normalize(rows)
    latest = df.sort_values(by='timestamp').groupby('alpha_name', as_index=False).tail(1)
    scores = {
        row['alpha_name']: score_alpha(float(row.get('hit_rate', 0.0)), float(row.get('avg_1h_return', 0.0)), float(row.get('avg_4h_return', 0.0)), float(row.get('avg_mae', 0.0)))
        for _, row in latest.iterrows()
    }
    new_weights = weight_store.update_from_scores(scores)
    logger.append({'event': 'weights', 'weights': new_weights, 'alpha_scores': scores, 'timestamp': utc_now(), 'update_applied': True, 'source': 'nightly_scheduler'})
    analytics.rebuild()
    return {'weights': new_weights, 'update_applied': True, 'alpha_scores': scores}


if __name__ == '__main__':
    print(run())
