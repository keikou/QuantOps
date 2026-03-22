from __future__ import annotations

from ai_hedge_bot.scheduler.rebalance_jobs import run_rebalance_job


def run_scheduler_cycle() -> dict:
    return {'status': 'ok', 'jobs': [run_rebalance_job()]}
