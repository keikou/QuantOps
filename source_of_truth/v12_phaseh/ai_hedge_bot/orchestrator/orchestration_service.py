from __future__ import annotations

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.orchestrator.cycle_runner import run_mode_cycle
from ai_hedge_bot.core.clock import utc_now_iso
from ai_hedge_bot.core.ids import new_cycle_id, new_signal_id
from ai_hedge_bot.data.storage.jsonl_logger import JsonlLogger


class OrchestrationService:
    def __init__(self) -> None:
        self._run_logger = JsonlLogger(CONTAINER.runtime_dir / 'logs' / 'orchestrator_runs.jsonl')
        self._cycle_logger = JsonlLogger(CONTAINER.runtime_dir / 'logs' / 'orchestrator_cycles.jsonl')
        self._order_logger = JsonlLogger(CONTAINER.runtime_dir / 'logs' / 'shadow_orders.jsonl')
        self._fill_logger = JsonlLogger(CONTAINER.runtime_dir / 'logs' / 'shadow_fills.jsonl')
        self._pnl_logger = JsonlLogger(CONTAINER.runtime_dir / 'logs' / 'shadow_pnl_snapshots.jsonl')
        self._quality_logger = JsonlLogger(CONTAINER.runtime_dir / 'logs' / 'execution_quality_snapshots.jsonl')

    def run(self, mode: str) -> dict:
        result = run_mode_cycle(mode)
        CONTAINER.latest_orchestrator_run = result
        created_at = result['timestamp']
        run_row = {
            'run_id': result['run_id'],
            'created_at': created_at,
            'mode': mode,
            'cycle_id': result['cycle_id'],
            'details_json': CONTAINER.runtime_store.to_json(result['details']),
        }
        cycle_row = {
            'cycle_id': result['cycle_id'],
            'created_at': created_at,
            'run_id': result['run_id'],
            'mode': mode,
            'status': result['status'],
        }
        CONTAINER.runtime_store.append('orchestrator_runs', run_row)
        CONTAINER.runtime_store.append('orchestrator_cycles', cycle_row)
        self._run_logger.append(run_row)
        self._cycle_logger.append(cycle_row)

        if mode == 'shadow':
            quality = self._record_shadow_runtime(result)
        elif mode == 'paper':
            quality = {
                'status': 'ok',
                'mode': 'paper',
                'fill_rate': 1.0,
                'avg_slippage_bps': 0.0,
                'latency_ms_p50': 0.0,
                'latency_ms_p95': 0.0,
            }
        else:
            quality = {
                'status': 'ok',
                'mode': mode,
                'fill_rate': None,
                'avg_slippage_bps': None,
                'latency_ms_p50': None,
                'latency_ms_p95': None,
            }
        CONTAINER.latest_execution_quality = quality
        return result

    def _record_shadow_runtime(self, result: dict) -> dict:
        decisions = CONTAINER.runtime_store.fetchall_dict(
            """
            SELECT symbol, side, target_weight
            FROM portfolio_signal_decisions
            WHERE created_at = (SELECT MAX(created_at) FROM portfolio_signal_decisions)
            ORDER BY symbol
            """
        )
        order_rows = []
        fill_rows = []
        total_slippage = 0.0
        for idx, decision in enumerate(decisions):
            oid = new_signal_id()
            qty = round(max(float(decision['target_weight']) * 1000.0, 1.0), 6)
            arrival_mid = 100.0 + idx * 5.0
            slippage = round(1.5 + idx * 0.4, 4)
            fill_price = round(arrival_mid * (1.0 + slippage / 10000.0), 6)
            order = {
                'shadow_order_id': oid,
                'created_at': result['timestamp'],
                'run_id': result['run_id'],
                'cycle_id': result['cycle_id'],
                'symbol': decision['symbol'],
                'side': decision['side'],
                'qty': qty,
                'status': 'filled',
                'arrival_mid_price': arrival_mid,
            }
            fill = {
                'fill_id': new_cycle_id(),
                'created_at': result['timestamp'],
                'shadow_order_id': oid,
                'symbol': decision['symbol'],
                'fill_qty': qty,
                'fill_price': fill_price,
                'slippage_bps': slippage,
                'fee_bps': 3.5,
            }
            order_rows.append(order)
            fill_rows.append(fill)
            total_slippage += slippage
            self._order_logger.append(order)
            self._fill_logger.append(fill)
        if order_rows:
            CONTAINER.runtime_store.append('shadow_orders', order_rows)
            CONTAINER.runtime_store.append('shadow_fills', fill_rows)
        fill_rate = round(len(fill_rows) / max(len(order_rows), 1), 4) if order_rows else 0.0
        avg_slippage = round(total_slippage / max(len(fill_rows), 1), 4) if fill_rows else 0.0
        latency_p50 = 42.0
        latency_p95 = 88.0
        quality_row = {
            'snapshot_id': new_cycle_id(),
            'created_at': result['timestamp'],
            'run_id': result['run_id'],
            'cycle_id': result['cycle_id'],
            'mode': 'shadow',
            'order_count': len(order_rows),
            'fill_count': len(fill_rows),
            'fill_rate': fill_rate,
            'avg_slippage_bps': avg_slippage,
            'latency_ms_p50': latency_p50,
            'latency_ms_p95': latency_p95,
        }
        CONTAINER.runtime_store.append('execution_quality_snapshots', quality_row)
        self._quality_logger.append(quality_row)

        pnl_row = {
            'snapshot_id': new_cycle_id(),
            'created_at': result['timestamp'],
            'run_id': result['run_id'],
            'cycle_id': result['cycle_id'],
            'order_count': len(order_rows),
            'fill_count': len(fill_rows),
            'gross_alpha_pnl_usd': round(1250.0 + len(fill_rows) * 10.0, 6),
            'net_shadow_pnl_usd': round(1210.0 + len(fill_rows) * 8.0, 6),
            'execution_drag_usd': 40.0,
            'slippage_drag_usd': round(avg_slippage * 2.0, 6),
            'fee_drag_usd': round(len(fill_rows) * 3.5, 6),
            'latency_drag_usd': 5.0,
        }
        CONTAINER.runtime_store.append('shadow_pnl_snapshots', pnl_row)
        self._pnl_logger.append(pnl_row)

        return {
            'status': 'ok',
            'mode': 'shadow',
            'fill_rate': fill_rate,
            'avg_slippage_bps': avg_slippage,
            'latency_ms_p50': latency_p50,
            'latency_ms_p95': latency_p95,
        }
