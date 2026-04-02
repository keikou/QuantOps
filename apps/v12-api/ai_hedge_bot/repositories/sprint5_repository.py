from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from ai_hedge_bot.app.container import CONTAINER


@dataclass
class Sprint5Repository:
    def __post_init__(self) -> None:
        self.store = CONTAINER.runtime_store

    def _active_position_snapshot_version(self) -> str | None:
        row = self.store.fetchone_dict(
            """
            SELECT version_id
            FROM position_snapshot_versions
            WHERE build_status = 'active'
            ORDER BY activated_at DESC, created_at DESC
            LIMIT 1
            """
        )
        version_id = str((row or {}).get('version_id') or '')
        if not version_id:
            return None
        count_row = self.store.fetchone_dict(
            "SELECT COUNT(*) AS cnt FROM position_snapshots_latest WHERE snapshot_version = ?",
            [version_id],
        ) or {'cnt': 0}
        active_rows = int(count_row.get('cnt', 0) or 0)
        if active_rows > 0:
            return version_id
        row_counts = self.store.fetchone_dict(
            """
            SELECT
                COUNT(*) AS total_rows,
                COUNT(snapshot_version) AS versioned_rows
            FROM position_snapshots_latest
            """
        ) or {'total_rows': 0, 'versioned_rows': 0}
        total_rows = int(row_counts.get('total_rows', 0) or 0)
        versioned_rows = int(row_counts.get('versioned_rows', 0) or 0)
        if total_rows == 0:
            return version_id
        return None if versioned_rows == 0 else version_id

    def _latest_market_price_map(self) -> dict[str, dict[str, Any]]:
        rows = self.store.fetchall_dict(
            """
            SELECT symbol, mark_price, source, price_time, quote_age_sec, stale
            FROM market_prices_latest
            """
        )
        return {str(row.get('symbol') or ''): row for row in rows}

    def _revalue_positions(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        price_by_symbol = self._latest_market_price_map()
        valued: list[dict[str, Any]] = []
        for row in rows:
            symbol = str(row.get('symbol') or '')
            signed_qty = float(row.get('signed_qty', 0.0) or 0.0)
            avg_entry_price = float(row.get('avg_entry_price', 0.0) or 0.0)
            price_meta = price_by_symbol.get(symbol) or {}
            mark_price = float(price_meta.get('mark_price', row.get('mark_price', avg_entry_price)) or avg_entry_price)
            market_value = round(signed_qty * mark_price, 8)
            unrealized_pnl = round((mark_price - avg_entry_price) * signed_qty, 8)
            valued.append(
                {
                    **row,
                    'mark_price': round(mark_price, 8),
                    'market_value': market_value,
                    'unrealized_pnl': unrealized_pnl,
                    'exposure_notional': round(abs(market_value), 8),
                    'price_source': price_meta.get('source', row.get('price_source')),
                    'quote_time': price_meta.get('price_time', row.get('quote_time')),
                    'quote_age_sec': float(price_meta.get('quote_age_sec', row.get('quote_age_sec', 0.0)) or 0.0),
                    'stale': bool(price_meta.get('stale', row.get('stale', False))),
                }
            )
        return valued

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
        active_version = self._active_position_snapshot_version()
        if active_version:
            latest_positions = self.store.fetchall_dict(
                """
                SELECT symbol, strategy_id, alpha_family, signed_qty, abs_qty, side, avg_entry_price,
                       mark_price, market_value, unrealized_pnl, realized_pnl, exposure_notional,
                       price_source, quote_time, quote_age_sec, stale, updated_at
                FROM position_snapshots_latest
                WHERE snapshot_version = ?
                ORDER BY exposure_notional DESC, symbol ASC
                """,
                [active_version],
            )
        else:
            latest_positions = self.store.fetchall_dict(
                """
                SELECT symbol, strategy_id, alpha_family, signed_qty, abs_qty, side, avg_entry_price,
                       mark_price, market_value, unrealized_pnl, realized_pnl, exposure_notional,
                       price_source, quote_time, quote_age_sec, stale, updated_at
                FROM position_snapshots_latest
                ORDER BY exposure_notional DESC, symbol ASC
                """
            )
        latest_positions = self._revalue_positions(latest_positions)
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

    def latest_portfolio_overview_summary(self) -> dict[str, Any]:
        equity = self.latest_equity_snapshot() or {}
        active_version = self._active_position_snapshot_version()
        if active_version:
            latest_positions = self.store.fetchall_dict(
                """
                SELECT symbol, strategy_id, alpha_family, exposure_notional, quote_time, stale
                FROM position_snapshots_latest
                WHERE snapshot_version = ?
                ORDER BY exposure_notional DESC, symbol ASC
                """,
                [active_version],
            )
        else:
            latest_positions = self.store.fetchall_dict(
                """
                SELECT symbol, strategy_id, alpha_family, exposure_notional, quote_time, stale
                FROM position_snapshots_latest
                ORDER BY exposure_notional DESC, symbol ASC
                """
            )
        latest_positions = self._revalue_positions(latest_positions)
        latest_run = self.store.fetchone_dict(
            """
            SELECT run_id, created_at
            FROM execution_fills
            ORDER BY created_at DESC
            LIMIT 1
            """
        ) or {}
        summary = {
            'total_equity': float(equity.get('total_equity', 0.0) or 0.0),
            'cash_balance': float(equity.get('cash_balance', 0.0) or 0.0),
            'free_cash': float(equity.get('free_cash', equity.get('cash_balance', 0.0)) or 0.0),
            'used_margin': float(equity.get('used_margin', 0.0) or 0.0),
            'collateral_equity': float(equity.get('collateral_equity', float(equity.get('free_cash', 0.0) or 0.0) + float(equity.get('used_margin', 0.0) or 0.0)) or 0.0),
            'available_margin': float(equity.get('available_margin', 0.0) or 0.0),
            'margin_utilization': float(equity.get('margin_utilization', 0.0) or 0.0),
            'gross_exposure': float(equity.get('gross_exposure', 0.0) or 0.0),
            'net_exposure': float(equity.get('net_exposure', 0.0) or 0.0),
            'long_exposure': float(equity.get('long_exposure', 0.0) or 0.0),
            'short_exposure': float(equity.get('short_exposure', 0.0) or 0.0),
            'realized_pnl': float(equity.get('realized_pnl', 0.0) or 0.0),
            'unrealized_pnl': float(equity.get('unrealized_pnl', 0.0) or 0.0),
            'fees_paid': float(equity.get('fees_paid', 0.0) or 0.0),
            'drawdown': float(equity.get('drawdown', 0.0) or 0.0),
            'as_of': equity.get('snapshot_time'),
            'quotes_as_of': max((row.get('quote_time') for row in latest_positions if row.get('quote_time')), default=None),
            'stale_positions': sum(1 for row in latest_positions if row.get('stale')),
            'position_row_count': len(latest_positions),
            'strategy_row_count': len({str(row.get('strategy_id') or '') for row in latest_positions}),
            'active_snapshot_version': active_version,
            'source_snapshot_time': equity.get('snapshot_time'),
        }
        return {
            'status': 'ok',
            'summary': summary,
            'snapshot': {
                'created_at': equity.get('snapshot_time') or latest_run.get('created_at'),
                'run_id': latest_run.get('run_id'),
                'target_count': len(latest_positions),
                'active_snapshot_version': active_version,
            },
            'positions': [],
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
        if latest and (latest.get('run_id') or latest.get('created_at')):
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

    def execution_quality_by_mode(self) -> dict[str, Any]:
        rows = self.store.fetchall_dict(
            """
            WITH latest_per_mode AS (
                SELECT mode, MAX(created_at) AS latest_created_at
                FROM execution_quality_snapshots
                GROUP BY mode
            )
            SELECT q.snapshot_id, q.created_at, q.run_id, q.cycle_id, q.mode, q.order_count, q.fill_count, q.fill_rate,
                   q.avg_slippage_bps, q.latency_ms_p50, q.latency_ms_p95
            FROM execution_quality_snapshots q
            INNER JOIN latest_per_mode lm
                ON q.mode = lm.mode AND q.created_at = lm.latest_created_at
            ORDER BY q.mode ASC
            """
        )
        items: list[dict[str, Any]] = []
        for row in rows:
            mode = str(row.get('mode') or 'unknown')
            run_id = row.get('run_id')
            route_rows = self.store.fetchall_dict(
                """
                SELECT route
                FROM execution_plans
                WHERE run_id = ?
                """,
                [run_id],
            )
            route_mix: dict[str, int] = {}
            for route_row in route_rows:
                route_key = str(route_row.get('route') or 'unknown')
                route_mix[route_key] = route_mix.get(route_key, 0) + 1
            items.append(
                {
                    'snapshot_id': row.get('snapshot_id'),
                    'created_at': row.get('created_at'),
                    'as_of': row.get('created_at'),
                    'run_id': run_id,
                    'cycle_id': row.get('cycle_id'),
                    'mode': mode,
                    'order_count': int(row.get('order_count', 0) or 0),
                    'fill_count': int(row.get('fill_count', 0) or 0),
                    'fill_rate': float(row.get('fill_rate', 0.0) or 0.0),
                    'avg_slippage_bps': float(row.get('avg_slippage_bps', 0.0) or 0.0),
                    'latency_ms_p50': float(row.get('latency_ms_p50', 0.0) or 0.0),
                    'latency_ms_p95': float(row.get('latency_ms_p95', 0.0) or 0.0),
                    'route_mix': route_mix,
                }
            )
        return {
            'status': 'ok',
            'items': items,
            'mode_count': len(items),
            'as_of': max((item.get('as_of') for item in items if item.get('as_of')), default=None),
        }

    def execution_latency_by_mode_route(self) -> dict[str, Any]:
        rows = self.store.fetchall_dict(
            """
            WITH latest_per_mode AS (
                SELECT mode, MAX(created_at) AS latest_created_at
                FROM execution_quality_snapshots
                GROUP BY mode
            ),
            latest_runs AS (
                SELECT q.mode, q.run_id, q.cycle_id
                FROM execution_quality_snapshots q
                INNER JOIN latest_per_mode lm
                    ON q.mode = lm.mode AND q.created_at = lm.latest_created_at
            )
            SELECT lr.mode,
                   lr.run_id,
                   lr.cycle_id,
                   COALESCE(p.route, 'unknown') AS route,
                   COUNT(*) AS fill_count,
                   AVG(COALESCE(f.latency_ms, 0.0)) AS avg_latency_ms,
                   MIN(COALESCE(f.latency_ms, 0.0)) AS latency_ms_p50,
                   MAX(COALESCE(f.latency_ms, 0.0)) AS latency_ms_p95
            FROM latest_runs lr
            INNER JOIN execution_fills f
                ON f.run_id = lr.run_id
            LEFT JOIN execution_plans p
                ON p.plan_id = f.plan_id
            GROUP BY lr.mode, lr.run_id, lr.cycle_id, COALESCE(p.route, 'unknown')
            ORDER BY lr.mode ASC, route ASC
            """
        )
        items = [
            {
                'mode': str(row.get('mode') or 'unknown'),
                'run_id': row.get('run_id'),
                'cycle_id': row.get('cycle_id'),
                'route': str(row.get('route') or 'unknown'),
                'fill_count': int(row.get('fill_count', 0) or 0),
                'avg_latency_ms': float(row.get('avg_latency_ms', 0.0) or 0.0),
                'latency_ms_p50': float(row.get('latency_ms_p50', 0.0) or 0.0),
                'latency_ms_p95': float(row.get('latency_ms_p95', 0.0) or 0.0),
            }
            for row in rows
        ]
        return {
            'status': 'ok',
            'items': items,
            'row_count': len(items),
            'as_of': max((item.get('run_id') for item in items if item.get('run_id')), default=None),
        }

    def latest_execution_pnl_linkage(self) -> dict[str, Any]:
        quality = self.latest_execution_quality_summary()
        overview = self.latest_portfolio_overview_summary()
        overview_summary = dict(overview.get('summary') or {})
        overview_snapshot = dict(overview.get('snapshot') or {})
        quality_run_id = quality.get('run_id')
        portfolio_run_id = overview_snapshot.get('run_id')
        realized_pnl = float(overview_summary.get('realized_pnl', 0.0) or 0.0)
        unrealized_pnl = float(overview_summary.get('unrealized_pnl', 0.0) or 0.0)
        fees_paid = float(overview_summary.get('fees_paid', 0.0) or 0.0)
        gross_pnl = realized_pnl + unrealized_pnl
        net_pnl_after_fees = gross_pnl - fees_paid
        return {
            'status': 'ok',
            'run_id': quality_run_id,
            'cycle_id': quality.get('cycle_id'),
            'mode': quality.get('mode'),
            'execution_quality': {
                'order_count': int(quality.get('order_count', 0) or 0),
                'fill_count': int(quality.get('fill_count', 0) or 0),
                'fill_rate': float(quality.get('fill_rate', 0.0) or 0.0),
                'avg_slippage_bps': float(quality.get('avg_slippage_bps', 0.0) or 0.0),
                'latency_ms_p50': float(quality.get('latency_ms_p50', 0.0) or 0.0),
                'latency_ms_p95': float(quality.get('latency_ms_p95', 0.0) or 0.0),
            },
            'portfolio_pnl': {
                'portfolio_run_id': portfolio_run_id,
                'total_equity': float(overview_summary.get('total_equity', 0.0) or 0.0),
                'realized_pnl': realized_pnl,
                'unrealized_pnl': unrealized_pnl,
                'gross_pnl': gross_pnl,
                'fees_paid': fees_paid,
                'net_pnl_after_fees': net_pnl_after_fees,
                'drawdown': float(overview_summary.get('drawdown', 0.0) or 0.0),
            },
            'linkage': {
                'portfolio_snapshot_run_id': portfolio_run_id,
                'run_id_match': bool(quality_run_id and portfolio_run_id and quality_run_id == portfolio_run_id),
                'has_execution_quality': bool(quality.get('run_id') or quality.get('as_of')),
                'has_portfolio_pnl': bool(overview_summary),
            },
            'as_of': quality.get('as_of') or overview.get('as_of'),
        }

    def latest_execution_drag_breakdown(self) -> dict[str, Any]:
        row = self.store.fetchone_dict(
            """
            SELECT run_id, created_at, gross_alpha_pnl_usd, net_shadow_pnl_usd,
                   execution_drag_usd, slippage_drag_usd, fee_drag_usd, latency_drag_usd
            FROM shadow_pnl_snapshots
            ORDER BY created_at DESC
            LIMIT 1
            """
        ) or {}
        quality = self.latest_execution_quality_summary()
        if not row:
            return {
                'status': 'ok',
                'run_id': quality.get('run_id'),
                'mode': quality.get('mode'),
                'drag': {
                    'gross_alpha_pnl_usd': 0.0,
                    'net_shadow_pnl_usd': 0.0,
                    'execution_drag_usd': 0.0,
                    'slippage_drag_usd': 0.0,
                    'fee_drag_usd': 0.0,
                    'latency_drag_usd': 0.0,
                    'component_sum_usd': 0.0,
                },
                'linkage': {
                    'quality_run_id': quality.get('run_id'),
                    'drag_run_id': None,
                    'run_id_match': False,
                },
                'as_of': quality.get('as_of'),
            }
        gross_alpha_pnl = float(row.get('gross_alpha_pnl_usd', 0.0) or 0.0)
        net_shadow_pnl = float(row.get('net_shadow_pnl_usd', 0.0) or 0.0)
        execution_drag = float(row.get('execution_drag_usd', 0.0) or 0.0)
        slippage_drag = float(row.get('slippage_drag_usd', 0.0) or 0.0)
        fee_drag = float(row.get('fee_drag_usd', 0.0) or 0.0)
        latency_drag = float(row.get('latency_drag_usd', 0.0) or 0.0)
        component_sum = slippage_drag + fee_drag + latency_drag
        return {
            'status': 'ok',
            'run_id': row.get('run_id'),
            'mode': quality.get('mode'),
            'drag': {
                'gross_alpha_pnl_usd': gross_alpha_pnl,
                'net_shadow_pnl_usd': net_shadow_pnl,
                'execution_drag_usd': execution_drag,
                'slippage_drag_usd': slippage_drag,
                'fee_drag_usd': fee_drag,
                'latency_drag_usd': latency_drag,
                'component_sum_usd': component_sum,
            },
            'linkage': {
                'quality_run_id': quality.get('run_id'),
                'drag_run_id': row.get('run_id'),
                'run_id_match': bool(quality.get('run_id') and quality.get('run_id') == row.get('run_id')),
            },
            'as_of': row.get('created_at') or quality.get('as_of'),
        }

    def latest_execution_symbol_leakage(self) -> dict[str, Any]:
        drag_payload = self.latest_execution_drag_breakdown()
        drag = dict(drag_payload.get('drag') or {})
        run_id = drag_payload.get('run_id')
        mode = drag_payload.get('mode')
        fills = self.store.fetchall_dict(
            """
            SELECT symbol, fill_qty, fill_price, slippage_bps, latency_ms, fee_bps
            FROM execution_fills
            WHERE run_id = ?
            ORDER BY symbol ASC
            """,
            [run_id],
        ) if run_id else []
        symbol_rows: dict[str, dict[str, Any]] = {}
        total_notional = 0.0
        for fill in fills:
            symbol = str(fill.get('symbol') or 'unknown')
            fill_qty = abs(float(fill.get('fill_qty', 0.0) or 0.0))
            fill_price = float(fill.get('fill_price', 0.0) or 0.0)
            notional = fill_qty * fill_price
            total_notional += notional
            row = symbol_rows.setdefault(
                symbol,
                {
                    'symbol': symbol,
                    'fill_count': 0,
                    'gross_notional_usd': 0.0,
                    'avg_slippage_bps': 0.0,
                    'avg_latency_ms': 0.0,
                    'avg_fee_bps': 0.0,
                },
            )
            row['fill_count'] += 1
            row['gross_notional_usd'] += notional
            row['avg_slippage_bps'] += float(fill.get('slippage_bps', 0.0) or 0.0)
            row['avg_latency_ms'] += float(fill.get('latency_ms', 0.0) or 0.0)
            row['avg_fee_bps'] += float(fill.get('fee_bps', 0.0) or 0.0)
        items: list[dict[str, Any]] = []
        total_slippage_drag = float(drag.get('slippage_drag_usd', 0.0) or 0.0)
        total_fee_drag = float(drag.get('fee_drag_usd', 0.0) or 0.0)
        total_latency_drag = float(drag.get('latency_drag_usd', 0.0) or 0.0)
        total_execution_drag = float(drag.get('execution_drag_usd', 0.0) or 0.0)
        for symbol in sorted(symbol_rows):
            row = symbol_rows[symbol]
            fill_count = max(int(row['fill_count']), 1)
            row['avg_slippage_bps'] = float(row['avg_slippage_bps']) / fill_count
            row['avg_latency_ms'] = float(row['avg_latency_ms']) / fill_count
            row['avg_fee_bps'] = float(row['avg_fee_bps']) / fill_count
            share = (float(row['gross_notional_usd']) / total_notional) if total_notional > 1e-9 else 0.0
            row['notional_share'] = share
            row['slippage_drag_usd'] = total_slippage_drag * share
            row['fee_drag_usd'] = total_fee_drag * share
            row['latency_drag_usd'] = total_latency_drag * share
            row['execution_drag_usd'] = total_execution_drag * share
            items.append(row)
        return {
            'status': 'ok',
            'run_id': run_id,
            'mode': mode,
            'items': items,
            'totals': {
                'gross_notional_usd': total_notional,
                'slippage_drag_usd': total_slippage_drag,
                'fee_drag_usd': total_fee_drag,
                'latency_drag_usd': total_latency_drag,
                'execution_drag_usd': total_execution_drag,
            },
            'as_of': drag_payload.get('as_of'),
        }

    def latest_execution_route_leakage(self) -> dict[str, Any]:
        drag_payload = self.latest_execution_drag_breakdown()
        drag = dict(drag_payload.get('drag') or {})
        run_id = drag_payload.get('run_id')
        mode = drag_payload.get('mode')
        fills = self.store.fetchall_dict(
            """
            SELECT f.symbol, f.fill_qty, f.fill_price, f.slippage_bps, f.latency_ms, f.fee_bps,
                   COALESCE(p.route, 'unknown') AS route
            FROM execution_fills f
            LEFT JOIN execution_plans p
                ON p.plan_id = f.plan_id
            WHERE f.run_id = ?
            ORDER BY route ASC, f.symbol ASC
            """,
            [run_id],
        ) if run_id else []
        route_rows: dict[str, dict[str, Any]] = {}
        total_notional = 0.0
        for fill in fills:
            route = str(fill.get('route') or 'unknown')
            fill_qty = abs(float(fill.get('fill_qty', 0.0) or 0.0))
            fill_price = float(fill.get('fill_price', 0.0) or 0.0)
            notional = fill_qty * fill_price
            total_notional += notional
            row = route_rows.setdefault(
                route,
                {
                    'route': route,
                    'fill_count': 0,
                    'gross_notional_usd': 0.0,
                    'avg_slippage_bps': 0.0,
                    'avg_latency_ms': 0.0,
                    'avg_fee_bps': 0.0,
                },
            )
            row['fill_count'] += 1
            row['gross_notional_usd'] += notional
            row['avg_slippage_bps'] += float(fill.get('slippage_bps', 0.0) or 0.0)
            row['avg_latency_ms'] += float(fill.get('latency_ms', 0.0) or 0.0)
            row['avg_fee_bps'] += float(fill.get('fee_bps', 0.0) or 0.0)
        items: list[dict[str, Any]] = []
        total_slippage_drag = float(drag.get('slippage_drag_usd', 0.0) or 0.0)
        total_fee_drag = float(drag.get('fee_drag_usd', 0.0) or 0.0)
        total_latency_drag = float(drag.get('latency_drag_usd', 0.0) or 0.0)
        total_execution_drag = float(drag.get('execution_drag_usd', 0.0) or 0.0)
        for route in sorted(route_rows):
            row = route_rows[route]
            fill_count = max(int(row['fill_count']), 1)
            row['avg_slippage_bps'] = float(row['avg_slippage_bps']) / fill_count
            row['avg_latency_ms'] = float(row['avg_latency_ms']) / fill_count
            row['avg_fee_bps'] = float(row['avg_fee_bps']) / fill_count
            share = (float(row['gross_notional_usd']) / total_notional) if total_notional > 1e-9 else 0.0
            row['notional_share'] = share
            row['slippage_drag_usd'] = total_slippage_drag * share
            row['fee_drag_usd'] = total_fee_drag * share
            row['latency_drag_usd'] = total_latency_drag * share
            row['execution_drag_usd'] = total_execution_drag * share
            items.append(row)
        return {
            'status': 'ok',
            'run_id': run_id,
            'mode': mode,
            'items': items,
            'totals': {
                'gross_notional_usd': total_notional,
                'slippage_drag_usd': total_slippage_drag,
                'fee_drag_usd': total_fee_drag,
                'latency_drag_usd': total_latency_drag,
                'execution_drag_usd': total_execution_drag,
            },
            'as_of': drag_payload.get('as_of'),
        }
