from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from ai_hedge_bot.app.container import CONTAINER


@dataclass
class Sprint5Repository:
    def __post_init__(self) -> None:
        self.store = CONTAINER.runtime_store

    def create_alpha_signal_snapshot(self, row: dict[str, Any]) -> None:
        self.store.append('alpha_signal_snapshots', row)

    def create_alpha_candidates(self, rows: list[dict[str, Any]]) -> None:
        self.store.append('alpha_candidates', rows)

    def create_portfolio_snapshot(self, row: dict[str, Any]) -> None:
        self.store.append('portfolio_snapshots', row)

    def create_portfolio_positions(self, rows: list[dict[str, Any]]) -> None:
        self.store.append('portfolio_positions', rows)

    def create_rebalance_plan(self, row: dict[str, Any]) -> None:
        self.store.append('rebalance_plans', row)

    def create_execution_plans(self, rows: list[dict[str, Any]]) -> None:
        self.store.append('execution_plans', rows)

    def create_execution_fills(self, rows: list[dict[str, Any]]) -> None:
        self.store.append('execution_fills', rows)

    def latest_equity_snapshot(self) -> dict[str, Any] | None:
        row = self.store.fetchone_dict(
            """
            SELECT snapshot_time, cash_balance, free_cash, used_margin, collateral_equity, available_margin, margin_utilization, gross_exposure, net_exposure, long_exposure, short_exposure,
                   market_value, unrealized_pnl, realized_pnl, fees_paid, total_equity, drawdown, peak_equity
            FROM equity_snapshots
            ORDER BY snapshot_time DESC
            LIMIT 1
            """
        )
        if not row:
            return None
        return row

    def latest_signal_snapshot(self) -> dict[str, Any]:
        row = self.store.fetchone_dict(
            """
            SELECT snapshot_id, created_at, run_id, mode, signal_count, symbols_json, summary_json
            FROM alpha_signal_snapshots
            ORDER BY created_at DESC
            LIMIT 1
            """
        )
        if not row:
            return {'status': 'ok', 'signal_count': 0, 'items': []}
        signal_rows = self.store.fetchall_dict(
            """
            SELECT signal_id, created_at, symbol, side, score, dominant_alpha, alpha_family, horizon,
                   turnover_profile, regime, metadata_json
            FROM signals
            WHERE created_at = (
                SELECT MAX(created_at) FROM signals
            )
            ORDER BY score DESC, symbol ASC
            """
        )
        for item in signal_rows:
            if item.get('metadata_json'):
                item['metadata'] = json.loads(item.pop('metadata_json'))
        return {
            'status': 'ok',
            'snapshot': {
                'snapshot_id': row['snapshot_id'],
                'created_at': row['created_at'],
                'run_id': row['run_id'],
                'mode': row['mode'],
                'signal_count': int(row['signal_count'] or 0),
                'symbols': json.loads(row['symbols_json']) if row.get('symbols_json') else [],
                'summary': json.loads(row['summary_json']) if row.get('summary_json') else {},
            },
            'items': signal_rows,
        }

    def latest_portfolio_overview(self) -> dict[str, Any]:
        equity = self.latest_equity_snapshot()
        latest_positions = self.store.fetchall_dict(
            """
            SELECT symbol, strategy_id, alpha_family, signed_qty, abs_qty, side, avg_entry_price,
                   mark_price, market_value, unrealized_pnl, realized_pnl, exposure_notional,
                   price_source, quote_time, quote_age_sec, stale, updated_at
            FROM position_snapshots_latest
            ORDER BY exposure_notional DESC, symbol ASC
            """
        )
        if equity or latest_positions:
            latest_run = self.store.fetchone_dict(
                """
                SELECT run_id, created_at
                FROM execution_fills
                ORDER BY created_at DESC
                LIMIT 1
                """
            ) or {}
            return {
                'status': 'ok',
                'summary': {
                    'total_equity': float((equity or {}).get('total_equity', 0.0) or 0.0),
                    'cash_balance': float((equity or {}).get('cash_balance', 0.0) or 0.0),
                    'free_cash': float((equity or {}).get('free_cash', (equity or {}).get('cash_balance', 0.0)) or 0.0),
                    'used_margin': float((equity or {}).get('used_margin', 0.0) or 0.0),
                    'collateral_equity': float((equity or {}).get('collateral_equity', (equity or {}).get('free_cash', 0.0) + (equity or {}).get('used_margin', 0.0)) or 0.0),
                    'available_margin': float((equity or {}).get('available_margin', 0.0) or 0.0),
                    'margin_utilization': float((equity or {}).get('margin_utilization', 0.0) or 0.0),
                    'gross_exposure': float((equity or {}).get('gross_exposure', 0.0) or 0.0),
                    'net_exposure': float((equity or {}).get('net_exposure', 0.0) or 0.0),
                    'long_exposure': float((equity or {}).get('long_exposure', 0.0) or 0.0),
                    'short_exposure': float((equity or {}).get('short_exposure', 0.0) or 0.0),
                    'realized_pnl': float((equity or {}).get('realized_pnl', 0.0) or 0.0),
                    'unrealized_pnl': float((equity or {}).get('unrealized_pnl', 0.0) or 0.0),
                    'fees_paid': float((equity or {}).get('fees_paid', 0.0) or 0.0),
                    'drawdown': float((equity or {}).get('drawdown', 0.0) or 0.0),
                    'as_of': (equity or {}).get('snapshot_time'),
                    'quotes_as_of': max((row.get('quote_time') for row in latest_positions if row.get('quote_time')), default=None),
                    'stale_positions': sum(1 for row in latest_positions if row.get('stale')),
                },
                'snapshot': {
                    'created_at': (equity or {}).get('snapshot_time') or latest_run.get('created_at'),
                    'gross_exposure': float((equity or {}).get('gross_exposure', 0.0) or 0.0),
                    'net_exposure': float((equity or {}).get('net_exposure', 0.0) or 0.0),
                    'cash_fraction': max(0.0, float((equity or {}).get('cash_balance', 0.0) or 0.0) / max(float((equity or {}).get('total_equity', 0.0) or 1.0), 1e-9)),
                    'run_id': latest_run.get('run_id'),
                    'target_count': len(latest_positions),
                },
                'positions': latest_positions,
            }
        snapshot = self.store.fetchone_dict(
            """
            SELECT snapshot_id, created_at, run_id, mode, target_count, gross_exposure, net_exposure,
                   turnover_estimate, cash_fraction, summary_json
            FROM portfolio_snapshots
            ORDER BY created_at DESC
            LIMIT 1
            """
        )
        if not snapshot:
            return {
                'status': 'ok',
                'snapshot': None,
                'positions': [],
            }
        positions = self.store.fetchall_dict(
            """
            SELECT position_id, created_at, run_id, mode, symbol, side, target_weight, notional_usd, source_signal_id
            FROM portfolio_positions
            WHERE run_id = ?
            ORDER BY ABS(target_weight) DESC, symbol ASC
            """,
            [snapshot['run_id']],
        )
        summary = json.loads(snapshot['summary_json']) if snapshot.get('summary_json') else {}
        return {
            'status': 'ok',
            'snapshot': {
                'snapshot_id': snapshot['snapshot_id'],
                'created_at': snapshot['created_at'],
                'run_id': snapshot['run_id'],
                'mode': snapshot['mode'],
                'target_count': int(snapshot['target_count'] or 0),
                'gross_exposure': float(snapshot['gross_exposure'] or 0.0),
                'net_exposure': float(snapshot['net_exposure'] or 0.0),
                'turnover_estimate': float(snapshot['turnover_estimate'] or 0.0),
                'cash_fraction': float(snapshot['cash_fraction'] or 0.0),
                'summary': summary,
            },
            'positions': positions,
        }

    def latest_execution_quality(self) -> dict[str, Any]:
        quality = self.store.fetchone_dict(
            """
            SELECT snapshot_id, created_at, run_id, cycle_id, mode, order_count, fill_count, fill_rate,
                   avg_slippage_bps, latency_ms_p50, latency_ms_p95
            FROM execution_quality_snapshots
            ORDER BY created_at DESC
            LIMIT 1
            """
        )
        if not quality:
            return {
                'status': 'ok',
                'order_count': 0,
                'fill_count': 0,
                'fill_rate': 0.0,
                'avg_slippage_bps': 0.0,
                'latency_ms_p50': 0.0,
                'latency_ms_p95': 0.0,
                'latest_fills': [],
            }
        fills = self.store.fetchall_dict(
            """
            SELECT fill_id, created_at, run_id, mode, plan_id, order_id, client_order_id, strategy_id, alpha_family,
                   symbol, side, fill_qty, fill_price, slippage_bps, latency_ms, fee_bps,
                   bid, ask, arrival_mid_price, price_source, quote_time, quote_age_sec, fallback_reason, status
            FROM execution_fills
            WHERE run_id = ?
            ORDER BY created_at DESC, symbol ASC
            LIMIT 20
            """,
            [quality['run_id']],
        )
        plans = self.store.fetchall_dict(
            """
            SELECT plan_id, created_at, run_id, mode, symbol, side, target_weight, order_qty, limit_price, participation_rate,
                   status, algo, route, expire_seconds, slice_count, metadata_json
            FROM execution_plans
            WHERE run_id = ?
            ORDER BY created_at DESC, symbol ASC
            LIMIT 20
            """,
            [quality['run_id']],
        )
        payload = dict(quality)
        payload['status'] = 'ok'
        payload['latest_fills'] = fills
        payload['latest_plans'] = plans
        payload['as_of'] = quality.get('created_at')
        return payload

    def latest_execution_quality_summary(self) -> dict[str, Any]:
        latest = dict(getattr(CONTAINER, 'latest_execution_quality', {}) or {})
        if latest:
            latest.setdefault('status', 'ok')
            latest.setdefault('as_of', latest.get('created_at'))
            return {
                'status': str(latest.get('status', 'ok') or 'ok'),
                'snapshot_id': latest.get('snapshot_id'),
                'created_at': latest.get('created_at'),
                'as_of': latest.get('as_of') or latest.get('created_at'),
                'run_id': latest.get('run_id'),
                'cycle_id': latest.get('cycle_id'),
                'mode': latest.get('mode'),
                'order_count': int(latest.get('order_count', 0) or 0),
                'fill_count': int(latest.get('fill_count', 0) or 0),
                'fill_rate': float(latest.get('fill_rate', 0.0) or 0.0),
                'avg_slippage_bps': float(latest.get('avg_slippage_bps', 0.0) or 0.0),
                'latency_ms_p50': float(latest.get('latency_ms_p50', 0.0) or 0.0),
                'latency_ms_p95': float(latest.get('latency_ms_p95', 0.0) or 0.0),
            }

        quality = self.store.fetchone_dict(
            """
            SELECT snapshot_id, created_at, run_id, cycle_id, mode, order_count, fill_count, fill_rate,
                   avg_slippage_bps, latency_ms_p50, latency_ms_p95
            FROM execution_quality_snapshots
            ORDER BY created_at DESC
            LIMIT 1
            """
        )
        if not quality:
            return {
                'status': 'ok',
                'order_count': 0,
                'fill_count': 0,
                'fill_rate': 0.0,
                'avg_slippage_bps': 0.0,
                'latency_ms_p50': 0.0,
                'latency_ms_p95': 0.0,
                'as_of': None,
            }
        payload = dict(quality)
        payload['status'] = 'ok'
        payload['as_of'] = quality.get('created_at')
        return payload
