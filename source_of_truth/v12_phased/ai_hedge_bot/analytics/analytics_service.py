from __future__ import annotations

from pathlib import Path
from ai_hedge_bot.data.storage.duckdb_store import DuckDBStore


class AnalyticsSyncService:
    TABLES = {
        'signals': 'signals.jsonl',
        'portfolio_diagnostics': 'portfolio_diagnostics.jsonl',
        'fills': 'fills.jsonl',
        'evaluations': 'evaluations.jsonl',
        'weight_updates': 'weight_updates.jsonl',
        'alpha_performance_summary': 'alpha_performance_summary.jsonl',
        'regime_performance_summary': 'regime_performance_summary.jsonl',
        'signal_expected_returns': 'signal_expected_returns.jsonl',
        'portfolio_weights': 'portfolio_weights.jsonl',
        'portfolio_allocations': 'portfolio_allocations.jsonl',
        'portfolio_risk_snapshots': 'portfolio_risk_snapshots.jsonl',
        'paper_runner_state': 'paper_runner_state.jsonl',
        'shadow_decisions': 'shadow_decisions.jsonl',
        'shadow_orders': 'shadow_orders.jsonl',
        'shadow_fills': 'shadow_fills.jsonl',
        'execution_costs': 'execution_costs.jsonl',
        'order_events': 'order_events.jsonl',
        'order_state_transitions': 'order_state_transitions.jsonl',
        'latency_snapshots': 'latency_snapshots.jsonl',
        'shadow_pnl_snapshots': 'shadow_pnl_snapshots.jsonl',
    }

    def __init__(self, db_path: Path, log_dir: Path) -> None:
        self.store = DuckDBStore(db_path)
        self.log_dir = log_dir

    def rebuild(self) -> dict[str, int]:
        counts = {}
        for table, filename in self.TABLES.items():
            counts[table] = self.store.sync_jsonl(table, self.log_dir / filename)
        return counts
