from __future__ import annotations

from time import perf_counter
from statistics import median

from ai_hedge_bot.app.container import CONTAINER
from ai_hedge_bot.contracts.reason_codes import (
    DEGRADED_MODE,
    EXECUTION_DISABLED,
    MISSING_PRICE,
    NO_POSITION_DELTA,
    ORDER_REJECTED,
    RISK_GUARD_BLOCK,
    STALE_MARKET_DATA,
    build_reason,
)
from ai_hedge_bot.contracts.runtime_events import FILL_RECORDED, ORDER_BLOCKED, ORDER_SUBMITTED, PLANNER_GENERATED, PORTFOLIO_UPDATED, build_runtime_event
from ai_hedge_bot.orchestrator.cycle_runner import run_mode_cycle
from ai_hedge_bot.core.ids import new_cycle_id, new_signal_id
from ai_hedge_bot.data.storage.jsonl_logger import JsonlLogger
from ai_hedge_bot.repositories.runtime_repository import RuntimeRepository
from ai_hedge_bot.repositories.sprint5_repository import Sprint5Repository
from ai_hedge_bot.signal.signal_service import SignalService
from ai_hedge_bot.portfolio.portfolio_service_phaseg import PhaseGPortfolioService
from ai_hedge_bot.services.truth_engine import TruthEngine
from ai_hedge_bot.execution.planner.execution_planner import ExecutionPlanner
from ai_hedge_bot.execution.state_machine import ExecutionStateInput, classify_execution_state, default_reason_codes


class OrchestrationService:
    def __init__(self) -> None:
        self._run_logger = JsonlLogger(CONTAINER.runtime_dir / 'logs' / 'orchestrator_runs.jsonl')
        self._cycle_logger = JsonlLogger(CONTAINER.runtime_dir / 'logs' / 'orchestrator_cycles.jsonl')
        self._writer_logger = JsonlLogger(CONTAINER.runtime_dir / 'logs' / 'writer_cycles.jsonl')
        self._order_logger = JsonlLogger(CONTAINER.runtime_dir / 'logs' / 'shadow_orders.jsonl')
        self._fill_logger = JsonlLogger(CONTAINER.runtime_dir / 'logs' / 'shadow_fills.jsonl')
        self._pnl_logger = JsonlLogger(CONTAINER.runtime_dir / 'logs' / 'shadow_pnl_snapshots.jsonl')
        self._quality_logger = JsonlLogger(CONTAINER.runtime_dir / 'logs' / 'execution_quality_snapshots.jsonl')
        self._signal_service = SignalService()
        self._portfolio_service = PhaseGPortfolioService()
        self._repo = Sprint5Repository()
        self._truth = TruthEngine()
        self._truth.ensure_schema()
        self._planner = ExecutionPlanner()
        self._runtime_repo = RuntimeRepository()

    def _cancel_open_execution_orders(self, reason: str) -> int:
        count_row = CONTAINER.runtime_store.fetchone_dict(
            """
            SELECT COUNT(*) AS cnt
            FROM execution_orders
            WHERE lower(coalesce(status, '')) IN ('submitted', 'partially_filled')
            """
        ) or {'cnt': 0}
        cancelled = int(count_row.get('cnt', 0) or 0)
        if cancelled > 0:
            CONTAINER.runtime_store.execute(
                """
                UPDATE execution_orders
                SET status = 'cancelled',
                    updated_at = current_timestamp
                WHERE lower(coalesce(status, '')) IN ('submitted', 'partially_filled')
                """
            )
        return cancelled

    def _append_runtime_events(self, rows: list[dict]) -> None:
        self._runtime_repo.create_events(rows)

    def _bridge_reason_event(
        self,
        *,
        result: dict,
        mode: str,
        code: str,
        summary: str,
        severity: str,
        symbol: str | None = None,
        details: dict | None = None,
    ) -> dict:
        payload = dict(details or {})
        payload.setdefault('blocking_component', 'execution_bridge')
        return build_runtime_event(
            event_type=ORDER_BLOCKED,
            run_id=result['run_id'],
            cycle_id=result['cycle_id'],
            mode=mode,
            source='execution_bridge',
            severity=severity,
            status='blocked',
            summary=summary,
            reason_code=code,
            symbol=symbol,
            details=payload,
            timestamp=result['timestamp'],
        )

    def run(self, mode: str, run_id: str | None = None, cycle_id: str | None = None) -> dict:
        run_started_at = perf_counter()
        self._truth.ensure_initial_capital()
        state_row = CONTAINER.runtime_store.fetchone_dict(
            "SELECT trading_state, note, CAST(created_at AS VARCHAR) AS as_of FROM runtime_control_state ORDER BY created_at DESC LIMIT 1"
        )
        trading_state = state_row or {'trading_state': 'running', 'as_of': None}
        state_name = str(trading_state.get('trading_state', 'running')).lower()
        if state_name in {'halted', 'paused'}:
            cancelled_orders = self._cancel_open_execution_orders(
                'risk_halted' if state_name == 'halted' else 'paused'
            )
            blocked_at = trading_state.get('as_of')
            self._record_execution_state(
                as_of=blocked_at,
                trading_state=state_name,
                active_plan_count=0,
                expired_plan_count=0,
                open_order_count=0,
                submitted_order_count=0,
                fill_count=0,
                latest_plan_id=None,
                latest_order_id=None,
                latest_fill_id=None,
                reasons=[{
                'code': 'risk_halted' if state_name == 'halted' else 'paused',
                'severity': 'critical' if state_name == 'halted' else 'high',
                'message': f"Execution blocked by trading_state={state_name}",
                'details': {**trading_state, 'cancelled_open_orders': cancelled_orders},
                }],
            )
            return {
                'status': 'blocked',
                'blocked': True,
                'message': f"orchestrator blocked: trading_state={state_name}",
                'run_id': run_id or new_cycle_id(),
                'cycle_id': new_cycle_id(),
                'timestamp': blocked_at,
                'details': {'trading_state': state_name, 'cancelled_open_orders': cancelled_orders},
            }
        result = run_mode_cycle(mode)
        if run_id:
            result['run_id'] = run_id
        if cycle_id:
            result['cycle_id'] = cycle_id
        signal_summary = self._record_signal_runtime(result, mode)
        portfolio_summary = self._record_portfolio_runtime(result, mode)
        prices = self._truth.synthesize_prices(portfolio_summary['decisions'], result['timestamp'], mode)
        self._truth.upsert_market_prices(prices, result['timestamp'])
        quality = self._record_execution_runtime(result, mode, portfolio_summary['decisions'], prices)
        record_started_at = perf_counter()
        self._truth.record_orders_and_fills(quality.get('latest_fills', []), result['timestamp'])
        order_fill_metrics = dict(self._truth.last_record_orders_and_fills_metrics)
        record_duration_ms = round((perf_counter() - record_started_at) * 1000.0, 2)
        rebuild_started_at = perf_counter()
        positions = self._truth.rebuild_positions(result['timestamp'])
        position_metrics = dict(self._truth.last_rebuild_positions_metrics)
        rebuild_duration_ms = round((perf_counter() - rebuild_started_at) * 1000.0, 2)
        equity_started_at = perf_counter()
        equity = self._truth.compute_equity_snapshot(positions, result['timestamp'])
        equity_metrics = dict(self._truth.last_compute_equity_snapshot_metrics)
        equity_duration_ms = round((perf_counter() - equity_started_at) * 1000.0, 2)
        result['details'].update({
            'signal_count': signal_summary['signal_count'],
            'target_count': portfolio_summary['target_count'],
            'fill_count': quality['fill_count'],
            'portfolio_gross_exposure': portfolio_summary['gross_exposure'],
            'total_equity': equity.get('total_equity', 0.0),
            'cash_balance': equity.get('cash_balance', 0.0),
        })
        writer_metrics = {
            'run_id': result['run_id'],
            'cycle_id': result['cycle_id'],
            'mode': mode,
            'as_of': result['timestamp'],
            'record_orders_and_fills_ms': record_duration_ms,
            'rebuild_positions_ms': rebuild_duration_ms,
            'compute_equity_snapshot_ms': equity_duration_ms,
            'cycle_duration_ms': round((perf_counter() - run_started_at) * 1000.0, 2),
            'fills_scanned_positions': position_metrics.get('fills_scanned', 0),
            'fills_scanned_equity': equity_metrics.get('fills_scanned', 0),
            'position_rows': position_metrics.get('position_rows', 0),
            'orders_written': order_fill_metrics.get('order_rows', 0),
            'fills_written': order_fill_metrics.get('fill_rows', 0),
            'cash_ledger_rows': order_fill_metrics.get('ledger_rows', 0),
            'position_snapshot_version': position_metrics.get('snapshot_version'),
            'position_build_duration_ms': position_metrics.get('build_duration_ms', 0.0),
            'position_full_rebuild_reason': position_metrics.get('full_rebuild_reason'),
            'position_fills_fetch_duration_ms': position_metrics.get('fills_fetch_duration_ms', 0.0),
            'position_price_fetch_duration_ms': position_metrics.get('price_fetch_duration_ms', 0.0),
            'position_state_build_duration_ms': position_metrics.get('state_build_duration_ms', 0.0),
            'position_version_insert_duration_ms': position_metrics.get('version_insert_duration_ms', 0.0),
            'position_row_materialize_duration_ms': position_metrics.get('row_materialize_duration_ms', 0.0),
            'position_row_write_duration_ms': position_metrics.get('row_write_duration_ms', 0.0),
            'position_activation_duration_ms': position_metrics.get('activation_duration_ms', 0.0),
            'position_cleanup_duration_ms': position_metrics.get('cleanup_duration_ms', 0.0),
            'position_history_rows_written': position_metrics.get('history_rows_written', 0),
            'equity_build_duration_ms': equity_metrics.get('build_duration_ms', 0.0),
            'equity_full_rebuild_reason': equity_metrics.get('full_rebuild_reason'),
        }
        result['details']['writer_metrics'] = writer_metrics
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
        self._writer_logger.append(writer_metrics)
        CONTAINER.latest_execution_quality = quality
        return result

    def _record_execution_state(
        self,
        *,
        as_of: str,
        trading_state: str,
        active_plan_count: int,
        expired_plan_count: int,
        open_order_count: int,
        submitted_order_count: int,
        fill_count: int,
        latest_plan_id: str | None,
        latest_order_id: str | None,
        latest_fill_id: str | None,
        reasons: list[dict],
        planner_age_sec: float | None = 0.0,
        execution_age_sec: float | None = 0.0,
        last_fill_age_sec: float | None = 0.0,
    ) -> None:
        state = classify_execution_state(
            ExecutionStateInput(
                trading_state=trading_state,
                active_plan_count=active_plan_count,
                expired_plan_count=expired_plan_count,
                open_order_count=open_order_count,
                submitted_order_count=submitted_order_count,
                fill_count=fill_count,
                planner_age_sec=planner_age_sec,
                execution_age_sec=execution_age_sec,
                last_fill_age_sec=last_fill_age_sec,
                reasons=tuple(str(item.get('code') or '') for item in reasons),
            )
        )
        CONTAINER.runtime_store.append('execution_state_snapshots', {
            'as_of': as_of,
            'trading_state': trading_state,
            'execution_state': state,
            'reason': reasons[0]['code'] if reasons else None,
            'planner_age_sec': planner_age_sec,
            'execution_age_sec': execution_age_sec,
            'last_fill_age_sec': last_fill_age_sec,
            'open_order_count': open_order_count,
            'active_plan_count': active_plan_count,
            'expired_plan_count': expired_plan_count,
            'latest_plan_id': latest_plan_id,
            'latest_order_id': latest_order_id,
            'latest_fill_id': latest_fill_id,
        })
        if reasons:
            CONTAINER.runtime_store.append('execution_block_reasons', [
                {
                    'as_of': as_of,
                    'code': str(item.get('code') or 'unknown'),
                    'severity': str(item.get('severity') or 'medium'),
                    'message': str(item.get('message') or ''),
                    'details_json': CONTAINER.runtime_store.to_json(item.get('details') or {}),
                }
                for item in reasons
            ])

    def _record_signal_runtime(self, result: dict, mode: str) -> dict:
        created_at = result['timestamp']
        signals = self._signal_service.generate(CONTAINER.config.symbols)
        rows = []
        eval_rows = []
        candidate_rows = []
        for idx, signal in enumerate(signals):
            row = {
                'signal_id': signal['signal_id'],
                'created_at': created_at,
                'symbol': signal['symbol'],
                'side': signal['side'],
                'score': float(signal['score']),
                'dominant_alpha': signal['dominant_alpha'],
                'alpha_family': signal['alpha_family'],
                'horizon': signal['horizon'],
                'turnover_profile': signal['turnover_profile'],
                'regime': signal['regime'],
                'metadata_json': CONTAINER.runtime_store.to_json(signal.get('metadata', {})),
            }
            rows.append(row)
            won = idx % 2 == 0
            ret_bps = round((signal['score'] - 0.5) * (100 if won else -60), 4)
            eval_rows.append({
                'evaluation_id': new_signal_id(),
                'signal_id': signal['signal_id'],
                'created_at': created_at,
                'symbol': signal['symbol'],
                'won': won,
                'return_bps': ret_bps,
            })
            candidate_rows.append({
                'candidate_id': new_signal_id(),
                'created_at': created_at,
                'strategy_id': 'global_multi_factor',
                'alpha_family': signal['alpha_family'],
                'symbol': signal['symbol'],
                'side': signal['side'],
                'score': float(signal['score']),
                'state': 'paper' if mode == 'paper' else 'shadow',
                'notes': signal['dominant_alpha'],
            })
        CONTAINER.runtime_store.append('signals', rows)
        CONTAINER.runtime_store.append('signal_evaluations', eval_rows)
        self._repo.create_alpha_candidates(candidate_rows)
        summary = {
            'top_symbol': max(signals, key=lambda x: x['score'])['symbol'] if signals else None,
            'avg_score': round(sum(float(s['score']) for s in signals) / max(len(signals), 1), 6),
        }
        self._repo.create_alpha_signal_snapshot({
            'snapshot_id': new_cycle_id(),
            'created_at': created_at,
            'run_id': result['run_id'],
            'mode': mode,
            'signal_count': len(signals),
            'symbols_json': CONTAINER.runtime_store.to_json([s['symbol'] for s in signals]),
            'summary_json': CONTAINER.runtime_store.to_json(summary),
        })
        return {'signal_count': len(signals), 'signals': signals}

    def _record_portfolio_runtime(self, result: dict, mode: str) -> dict:
        created_at = result['timestamp']
        rows = CONTAINER.runtime_store.fetchall_dict(
            """
            SELECT signal_id, symbol, side, score, dominant_alpha, alpha_family, horizon, turnover_profile, regime
            FROM signals
            WHERE created_at = ?
            ORDER BY symbol
            """,
            [created_at],
        )
        signals = [dict(row, metadata={}) for row in rows]
        prepared = self._portfolio_service.prepare(signals)
        diag_row = {
            'diagnostics_id': new_cycle_id(),
            'created_at': created_at,
            'input_signals': prepared['diagnostics']['input_signals'],
            'kept_signals': prepared['diagnostics']['kept_signals'],
            'crowding_flags_json': CONTAINER.runtime_store.to_json(prepared['diagnostics']['crowding_flags']),
            'overlap_penalty_applied': prepared['diagnostics']['overlap_penalty_applied'],
        }
        CONTAINER.runtime_store.append('portfolio_diagnostics', diag_row)
        decisions = []
        positions = []
        gross = 0.0
        net = 0.0
        for decision in prepared['decisions']:
            weight = float(decision['target_weight'])
            gross += abs(weight)
            net += weight if decision['side'] == 'long' else -weight
            decision_row = {
                'decision_id': new_signal_id(),
                'signal_id': decision['signal_id'],
                'created_at': created_at,
                'symbol': decision['symbol'],
                'side': decision['side'],
                'target_weight': weight,
            }
            decisions.append(decision_row)
            positions.append({
                'position_id': new_signal_id(),
                'created_at': created_at,
                'run_id': result['run_id'],
                'mode': mode,
                'symbol': decision['symbol'],
                'side': decision['side'],
                'target_weight': weight,
                'notional_usd': round(weight * 100000.0, 6),
                'source_signal_id': decision['signal_id'],
            })
        CONTAINER.runtime_store.append('portfolio_signal_decisions', decisions)
        self._repo.create_portfolio_positions(positions)
        turnover_estimate = round(gross * 0.5, 6)
        cash_fraction = round(max(0.0, 1.0 - gross), 6)
        summary = {
            'kept_signals': prepared['diagnostics']['kept_signals'],
            'crowding_flags': prepared['diagnostics']['crowding_flags'],
        }
        self._repo.create_portfolio_snapshot({
            'snapshot_id': new_cycle_id(),
            'created_at': created_at,
            'run_id': result['run_id'],
            'mode': mode,
            'target_count': len(positions),
            'gross_exposure': round(gross, 6),
            'net_exposure': round(net, 6),
            'turnover_estimate': turnover_estimate,
            'cash_fraction': cash_fraction,
            'summary_json': CONTAINER.runtime_store.to_json(summary),
        })
        self._repo.create_rebalance_plan({
            'plan_id': new_cycle_id(),
            'created_at': created_at,
            'run_id': result['run_id'],
            'mode': mode,
            'action_count': len(positions),
            'gross_delta': round(gross, 6),
            'summary_json': CONTAINER.runtime_store.to_json({'target_symbols': [p['symbol'] for p in positions]}),
        })
        CONTAINER.latest_portfolio_diagnostics = prepared['diagnostics']
        self._append_runtime_events([
            build_runtime_event(
                event_type=PORTFOLIO_UPDATED,
                run_id=result['run_id'],
                cycle_id=result['cycle_id'],
                mode=mode,
                source='orchestration_service',
                summary=f"Portfolio updated with {len(positions)} target positions.",
                details={
                    'target_count': len(positions),
                    'gross_exposure': round(gross, 6),
                    'cash_fraction': cash_fraction,
                },
                timestamp=created_at,
            )
        ])
        return {'decisions': decisions, 'target_count': len(positions), 'gross_exposure': round(gross, 6)}

    def _record_execution_runtime(self, result: dict, mode: str, decisions: list[dict], market_prices: list[dict] | None = None) -> dict:
        created_at = result['timestamp']
        state_row = CONTAINER.runtime_store.fetchone_dict(
            "SELECT trading_state, note, CAST(created_at AS VARCHAR) AS as_of FROM runtime_control_state ORDER BY created_at DESC LIMIT 1"
        )
        trading_state = str((state_row or {}).get('trading_state', 'running') or 'running').lower()
        if trading_state in {'halted', 'paused'}:
            cancelled_orders = self._cancel_open_execution_orders('risk_halted' if trading_state == 'halted' else 'paused')
            blocked_reason = build_reason(
                EXECUTION_DISABLED,
                detail={**(state_row or {}), 'cancelled_open_orders': cancelled_orders},
            )
            reasons = [{
                'code': blocked_reason['code'],
                'severity': blocked_reason['severity'],
                'message': blocked_reason['message'],
                'details': blocked_reason['details'],
            }]
            self._record_execution_state(
                as_of=created_at,
                trading_state=trading_state,
                active_plan_count=0,
                expired_plan_count=0,
                open_order_count=0,
                submitted_order_count=0,
                fill_count=0,
                latest_plan_id=None,
                latest_order_id=None,
                latest_fill_id=None,
                reasons=reasons,
            )
            return {
                'status': 'blocked',
                'mode': mode,
                'order_count': 0,
                'fill_count': 0,
                'fill_rate': 0.0,
                'avg_slippage_bps': 0.0,
                'latency_ms_p50': 0.0,
                'latency_ms_p95': 0.0,
                'latest_fills': [],
                'blocked': True,
                'cancelled_open_orders': cancelled_orders,
            }

        plans = []
        fills = []
        orders = []
        blocked_events = []
        shadow_orders = []
        shadow_fills = []
        latencies = []
        total_slippage = 0.0
        price_map = {str(item['symbol']): item for item in (market_prices or [])}
        active_snapshot_version = self._active_position_snapshot_version()
        position_rows = (
            CONTAINER.runtime_store.fetchall_dict(
                "SELECT symbol, SUM(signed_qty) AS signed_qty FROM position_snapshots_latest WHERE snapshot_version = ? GROUP BY symbol",
                [active_snapshot_version],
            )
            if active_snapshot_version
            else CONTAINER.runtime_store.fetchall_dict(
                "SELECT symbol, SUM(signed_qty) AS signed_qty FROM position_snapshots_latest GROUP BY symbol"
            )
        )
        current_positions = {
            str(row['symbol']): float(row.get('signed_qty', 0.0) or 0.0)
            for row in position_rows
        }
        latest_equity_row = CONTAINER.runtime_store.fetchone_dict(
            "SELECT total_equity, available_margin FROM equity_snapshots ORDER BY snapshot_time DESC LIMIT 1"
        )
        capital_base = float((latest_equity_row or {}).get('total_equity', 0.0) or 0.0)
        available_margin = float((latest_equity_row or {}).get('available_margin', capital_base) or capital_base)
        capital_base = capital_base if capital_base > 1000.0 else self._truth.initial_capital
        if not decisions:
            blocked_events.append(
                self._bridge_reason_event(
                    result=result,
                    mode=mode,
                    code=NO_POSITION_DELTA,
                    summary='Planner received no actionable portfolio decisions.',
                    severity='info',
                    details={
                        'decision_count': 0,
                        'input_snapshot': {
                            'capital_base': capital_base,
                            'available_margin': available_margin,
                        },
                    },
                )
            )
        for idx, decision in enumerate(decisions):
            weight = float(decision['target_weight'])
            quote = price_map.get(str(decision['symbol'])) or {}
            used_price_fallback = str(decision['symbol']) not in price_map
            if used_price_fallback:
                blocked_events.append(
                    self._bridge_reason_event(
                        result=result,
                        mode=mode,
                        code=MISSING_PRICE,
                        summary=f"Missing live quote for {decision['symbol']}; using synthetic fallback pricing.",
                        severity='high',
                        symbol=decision['symbol'],
                        details={
                            'blocking_component': 'execution_planner',
                            'decision_snapshot': {
                                'side': decision['side'],
                                'target_weight': decision['target_weight'],
                            },
                        },
                    )
                )
            arrival_mid = float(quote.get('mid', 100.0 + idx * 5.0) or (100.0 + idx * 5.0))
            bid = float(quote.get('bid', arrival_mid) or arrival_mid)
            ask = float(quote.get('ask', arrival_mid) or arrival_mid)
            signed_target_weight = abs(weight) if decision['side'] == 'long' else -abs(weight)
            target_notional = signed_target_weight * capital_base
            target_signed_qty = target_notional / max(arrival_mid, 1e-9)
            current_signed_qty = float(current_positions.get(str(decision['symbol']), 0.0) or 0.0)
            delta_qty = target_signed_qty - current_signed_qty
            if abs(delta_qty) * arrival_mid < 25.0:
                blocked_events.append(
                    self._bridge_reason_event(
                        result=result,
                        mode=mode,
                        code=NO_POSITION_DELTA,
                        summary=f"No actionable delta for {decision['symbol']}.",
                        severity='info',
                        symbol=decision['symbol'],
                        details={
                            'blocking_component': 'execution_planner',
                            'arrival_mid': arrival_mid,
                            'target_signed_qty': target_signed_qty,
                            'current_signed_qty': current_signed_qty,
                            'delta_qty': delta_qty,
                            'decision_snapshot': {
                                'side': decision['side'],
                                'target_weight': decision['target_weight'],
                            },
                        },
                    )
                )
                continue
            qty = round(max(abs(delta_qty), 1e-6), 8)
            trade_side = 'buy' if delta_qty > 0 else 'sell'
            slippage = round((0.8 if mode == 'paper' else 1.5) + idx * 0.4, 4)
            latency = round((20.0 if mode == 'paper' else 42.0) + idx * 7.0, 4)
            fee_bps = 1.0 if mode == 'paper' else 3.5
            direction = 1.0 if trade_side == 'buy' else -1.0
            fill_price = round(arrival_mid * (1.0 + direction * slippage / 10000.0), 8)
            plan_id = new_cycle_id()
            participation_rate = round(min(0.2, 0.05 + idx * 0.02), 4)
            observed_volume = float(quote.get('volume_qty') or quote.get('estimated_volume_qty') or 0.0)
            required_margin = qty * arrival_mid
            if available_margin > 0.0 and required_margin > available_margin:
                qty = round(max(available_margin / max(arrival_mid, 1e-9), 0.0), 8)
                required_margin = qty * arrival_mid
                if qty <= 0.0:
                    blocked_events.append(
                        self._bridge_reason_event(
                            result=result,
                            mode=mode,
                            code=RISK_GUARD_BLOCK,
                            summary=f"Risk guard blocked {decision['symbol']} due to margin limits.",
                            severity='high',
                            symbol=decision['symbol'],
                            details={
                                'blocking_component': 'risk_guard',
                                'arrival_mid': arrival_mid,
                                'required_margin': required_margin,
                                'available_margin': available_margin,
                                'decision_snapshot': {
                                    'side': decision['side'],
                                    'target_weight': decision['target_weight'],
                                },
                            },
                        )
                    )
                    continue
            plan_meta = self._planner.build_plan(
                symbol=decision['symbol'],
                side=trade_side,
                qty=qty,
                arrival_mid=arrival_mid,
                bid=bid,
                ask=ask,
                quote_age_sec=float(quote.get('quote_age_sec', 0.0) or 0.0),
                mode=mode,
                participation_rate=participation_rate,
                alpha_horizon=decision.get('horizon'),
                observed_volume=observed_volume,
                available_margin=available_margin,
                required_margin=required_margin,
            )
            plans.append({
                'plan_id': plan_id,
                'created_at': created_at,
                'run_id': result['run_id'],
                'mode': mode,
                'symbol': decision['symbol'],
                'side': trade_side,
                'target_weight': signed_target_weight,
                'order_qty': qty,
                'limit_price': arrival_mid,
                'participation_rate': participation_rate,
                'status': 'planned',
                'algo': plan_meta['algo'],
                'route': plan_meta['route'],
                'expire_seconds': plan_meta['expire_seconds'],
                'slice_count': plan_meta['slice_count'],
                'metadata_json': CONTAINER.runtime_store.to_json(plan_meta),
            })
            if plan_meta.get('stale_quote'):
                blocked_events.append(
                    self._bridge_reason_event(
                        result=result,
                        mode=mode,
                        code=STALE_MARKET_DATA,
                        summary=f"Stale quote degraded execution for {decision['symbol']}.",
                        severity='high',
                        symbol=decision['symbol'],
                        details={
                            'blocking_component': 'execution_planner',
                            'plan_id': plan_id,
                            'quote_age_sec': plan_meta.get('quote_age_sec'),
                            'plan_snapshot': {
                                'algo': plan_meta.get('algo'),
                                'route': plan_meta.get('route'),
                                'slice_count': plan_meta.get('slice_count'),
                            },
                        },
                    )
                )
            child_orders = list(plan_meta.get('child_orders') or [{'child_index': 1, 'child_qty': qty, 'route': plan_meta['route'], 'style': plan_meta['algo'], 'time_bucket_sec': 0}])
            observed_volume_qty = float(plan_meta.get('observed_volume_qty', 0.0) or 0.0)
            submitted_count = 0
            for child_idx, child in enumerate(child_orders):
                child_qty = float(child.get('child_qty', 0.0) or 0.0)
                if child_qty <= 0.0:
                    continue
                order_id = f"{plan_id}_child_{child_idx+1}"
                child_latency = round(latency + child_idx * (6.0 if plan_meta['algo'] == 'twap' else 4.0), 4)
                child_slippage = round(slippage + (0.25 * child_idx if plan_meta['algo'] == 'aggressive_limit' else 0.12 * child_idx), 4)
                venue = 'paper_simulator'
                route = str(child.get('route') or plan_meta['route'])
                style = str(child.get('style') or plan_meta['algo'])
                status = 'submitted'
                fill_ratio = 1.0
                if style == 'pov' and observed_volume_qty > 0.0:
                    fill_ratio = min(1.0, max(0.35, observed_volume_qty * max(participation_rate, 0.01) / max(child_qty, 1e-9)))
                    if fill_ratio < 0.999:
                        status = 'partially_filled'
                if plan_meta.get('stale_quote') and child_idx == len(child_orders) - 1 and style != 'aggressive_limit':
                    status = 'cancelled'
                    fill_ratio = 0.0
                submitted_count += 1
                orders.append({
                    'order_id': order_id,
                    'plan_id': plan_id,
                    'parent_order_id': plan_id,
                    'client_order_id': order_id,
                    'strategy_id': result['run_id'],
                    'alpha_family': decision.get('alpha_family', 'runtime'),
                    'symbol': decision['symbol'],
                    'side': trade_side,
                    'order_type': f'paper_{style}',
                    'qty': child_qty,
                    'limit_price': arrival_mid,
                    'venue': venue,
                    'route': route,
                    'algo': style,
                    'submit_time': created_at,
                    'status': status,
                    'source': 'orchestrator',
                    'metadata_json': CONTAINER.runtime_store.to_json({'child_index': child_idx + 1, 'time_bucket_sec': child.get('time_bucket_sec', 0), 'plan': plan_meta}),
                    'created_at': created_at,
                    'updated_at': created_at,
                })
                fill_qty = round(child_qty * fill_ratio, 8)
                if fill_qty <= 0.0:
                    continue
                child_fill_price = round(arrival_mid * (1.0 + direction * child_slippage / 10000.0), 8)
                fill = {
                    'fill_id': new_cycle_id(),
                    'order_id': order_id,
                    'client_order_id': order_id,
                    'strategy_id': result['run_id'],
                    'alpha_family': decision.get('alpha_family', 'runtime'),
                    'created_at': created_at,
                    'run_id': result['run_id'],
                    'mode': mode,
                    'plan_id': plan_id,
                    'symbol': decision['symbol'],
                    'side': trade_side,
                    'fill_qty': fill_qty,
                    'fill_price': child_fill_price,
                    'slippage_bps': child_slippage,
                    'latency_ms': child_latency,
                    'fee_bps': fee_bps,
                    'bid': bid,
                    'ask': ask,
                    'arrival_mid_price': arrival_mid,
                    'price_source': quote.get('source', f'{mode}_synthetic_quote_fallback'),
                    'quote_time': quote.get('quote_time', created_at),
                    'quote_age_sec': float(quote.get('quote_age_sec', 0.0) or 0.0),
                    'fallback_reason': quote.get('fallback_reason'),
                    'status': 'filled' if fill_ratio >= 0.999 else 'partial_fill',
                }
                fills.append(fill)
                total_slippage += child_slippage
                latencies.append(child_latency)
            filled_signed_qty = sum(
                float(f.get('fill_qty', 0.0) or 0.0) * (1.0 if trade_side == 'buy' else -1.0)
                for f in fills if f.get('plan_id') == plan_id
            )
            current_positions[str(decision['symbol'])] = current_signed_qty + filled_signed_qty
            if mode == 'shadow':
                order = {
                    'shadow_order_id': plan_id,
                    'created_at': created_at,
                    'run_id': result['run_id'],
                    'cycle_id': result['cycle_id'],
                    'symbol': decision['symbol'],
                    'side': decision['side'],
                    'qty': qty,
                    'status': 'filled',
                    'arrival_mid_price': arrival_mid,
                }
                shadow_fill = {
                    'fill_id': fill['fill_id'],
                    'created_at': created_at,
                    'shadow_order_id': plan_id,
                    'symbol': decision['symbol'],
                    'fill_qty': qty,
                    'fill_price': fill_price,
                    'slippage_bps': slippage,
                    'fee_bps': fee_bps,
                }
                shadow_orders.append(order)
                shadow_fills.append(shadow_fill)
                self._order_logger.append(order)
                self._fill_logger.append(shadow_fill)
        self._repo.create_execution_plans(plans)
        self._repo.create_execution_fills(fills)
        if orders:
            CONTAINER.runtime_store.append('execution_orders', orders)
        if shadow_orders:
            CONTAINER.runtime_store.append('shadow_orders', shadow_orders)
            CONTAINER.runtime_store.append('shadow_fills', shadow_fills)
        submitted_qty = sum(abs(float(order.get('qty', 0.0) or 0.0)) for order in orders)
        filled_qty = sum(abs(float(fill.get('fill_qty', 0.0) or 0.0)) for fill in fills)
        child_order_count = len(orders)
        child_fill_count = len(fills)
        raw_fill_rate = (filled_qty / submitted_qty) if submitted_qty > 0 else ((child_fill_count / max(child_order_count, 1)) if child_order_count > 0 else 0.0)
        fill_rate = round(max(0.0, min(1.0, raw_fill_rate)), 4)
        avg_slippage = round(total_slippage / max(child_fill_count, 1), 4) if fills else 0.0
        latency_p50 = float(median(latencies)) if latencies else 0.0
        latency_p95 = float(max(latencies)) if latencies else 0.0
        quality_row = {
            'snapshot_id': new_cycle_id(),
            'created_at': created_at,
            'run_id': result['run_id'],
            'cycle_id': result['cycle_id'],
            'mode': mode,
            'order_count': child_order_count,
            'fill_count': child_fill_count,
            'fill_rate': fill_rate,
            'avg_slippage_bps': avg_slippage,
            'latency_ms_p50': latency_p50,
            'latency_ms_p95': latency_p95,
        }
        CONTAINER.runtime_store.append('execution_quality_snapshots', quality_row)
        self._quality_logger.append(quality_row)
        latest_plan_id = plans[-1]['plan_id'] if plans else None
        latest_order_id = orders[-1]['order_id'] if orders else None
        latest_fill_id = fills[-1]['fill_id'] if fills else None
        reasons = default_reason_codes(
            ExecutionStateInput(
                trading_state='running',
                active_plan_count=len(plans),
                expired_plan_count=0,
                open_order_count=sum(1 for order in orders if str(order.get('status')) in {'submitted', 'partially_filled'}),
                submitted_order_count=len(orders),
                fill_count=len(fills),
                planner_age_sec=0.0,
                execution_age_sec=0.0,
                last_fill_age_sec=0.0,
            )
        )
        self._record_execution_state(
            as_of=created_at,
            trading_state='running',
            active_plan_count=len(plans),
            expired_plan_count=0,
            open_order_count=sum(1 for order in orders if str(order.get('status')) in {'submitted', 'partially_filled'}),
            submitted_order_count=len(orders),
            fill_count=len(fills),
            latest_plan_id=latest_plan_id,
            latest_order_id=latest_order_id,
            latest_fill_id=latest_fill_id,
            reasons=reasons,
        )
        runtime_events: list[dict] = []
        planner_status = 'ok'
        planner_severity = 'info'
        planner_summary = f"Planner generated {len(plans)} execution plans."
        planner_reason_code = None
        if not plans:
            planner_status = 'blocked'
            planner_severity = 'info'
            planner_summary = 'Planner generated zero execution plans.'
            planner_reason_code = NO_POSITION_DELTA if decisions == [] else (blocked_events[0].get('reason_code') if blocked_events else NO_POSITION_DELTA)
        elif child_order_count == 0:
            planner_status = 'blocked'
            planner_severity = 'high'
            planner_summary = 'Planner generated plans but bridge submitted zero child orders.'
            planner_reason_code = blocked_events[0].get('reason_code') if blocked_events else DEGRADED_MODE
        runtime_events.append(
            build_runtime_event(
                event_type=PLANNER_GENERATED,
                run_id=result['run_id'],
                cycle_id=result['cycle_id'],
                mode=mode,
                source='execution_planner',
                status=planner_status,
                severity=planner_severity,
                summary=planner_summary,
                reason_code=planner_reason_code,
                details={
                    'decision_count': len(decisions),
                    'plan_count': len(plans),
                    'order_count': child_order_count,
                    'fill_count': child_fill_count,
                    'blocked_count': len(blocked_events),
                },
                timestamp=created_at,
            )
        )
        if plans and child_order_count == 0:
            runtime_events.append(
                self._bridge_reason_event(
                    result=result,
                    mode=mode,
                    code=blocked_events[0].get('reason_code') if blocked_events else DEGRADED_MODE,
                    summary='Execution bridge produced zero child orders for generated plans.',
                    severity='high',
                    symbol=plans[0].get('symbol') if len(plans) == 1 else None,
                    details={
                        'plan_count': len(plans),
                        'blocked_count': len(blocked_events),
                        'blocking_component': 'execution_bridge',
                    },
                )
            )
        if child_order_count > 0 and child_fill_count == 0:
            runtime_events.append(
                self._bridge_reason_event(
                    result=result,
                    mode=mode,
                    code=ORDER_REJECTED,
                    summary='Child orders were submitted but no fills were recorded.',
                    severity='high',
                    details={
                        'order_count': child_order_count,
                        'fill_count': child_fill_count,
                        'blocking_component': 'execution_bridge',
                    },
                )
            )
        runtime_events.extend(
            build_runtime_event(
                event_type=ORDER_SUBMITTED,
                run_id=result['run_id'],
                cycle_id=result['cycle_id'],
                mode=mode,
                source='execution_planner',
                status='ok',
                summary=f"Submitted {order['side']} {order['symbol']} order.",
                symbol=order['symbol'],
                details={
                    'order_id': order['order_id'],
                    'plan_id': order['plan_id'],
                    'qty': order['qty'],
                    'status': order['status'],
                },
                timestamp=created_at,
            )
            for order in orders
        )
        runtime_events.extend(
            build_runtime_event(
                event_type=FILL_RECORDED,
                run_id=result['run_id'],
                cycle_id=result['cycle_id'],
                mode=mode,
                source='execution_bridge',
                status='ok',
                summary=f"Recorded fill for {fill['symbol']}.",
                symbol=fill['symbol'],
                details={
                    'fill_id': fill['fill_id'],
                    'plan_id': fill['plan_id'],
                    'order_id': fill['order_id'],
                    'fill_qty': fill['fill_qty'],
                    'fill_price': fill['fill_price'],
                },
                timestamp=created_at,
            )
            for fill in fills
        )
        runtime_events.extend(blocked_events)
        self._append_runtime_events(runtime_events)
        if mode == 'shadow':
            pnl_row = {
                'snapshot_id': new_cycle_id(),
                'created_at': created_at,
                'run_id': result['run_id'],
                'cycle_id': result['cycle_id'],
                'order_count': len(plans),
                'fill_count': len(fills),
                'gross_alpha_pnl_usd': round(1250.0 + len(fills) * 10.0, 6),
                'net_shadow_pnl_usd': round(1210.0 + len(fills) * 8.0, 6),
                'execution_drag_usd': 40.0,
                'slippage_drag_usd': round(avg_slippage * 2.0, 6),
                'fee_drag_usd': round(len(fills) * 3.5, 6),
                'latency_drag_usd': 5.0,
            }
            CONTAINER.runtime_store.append('shadow_pnl_snapshots', pnl_row)
            self._pnl_logger.append(pnl_row)
        return {
            'status': 'ok',
            'mode': mode,
            'order_count': child_order_count,
            'fill_count': child_fill_count,
            'fill_rate': fill_rate,
            'avg_slippage_bps': avg_slippage,
            'latency_ms_p50': latency_p50,
            'latency_ms_p95': latency_p95,
            'latest_fills': fills,
        }
    def _active_position_snapshot_version(self) -> str | None:
        row = CONTAINER.runtime_store.fetchone_dict(
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
        count_row = CONTAINER.runtime_store.fetchone_dict(
            "SELECT COUNT(*) AS cnt FROM position_snapshots_latest WHERE snapshot_version = ?",
            [version_id],
        ) or {'cnt': 0}
        active_rows = int(count_row.get('cnt', 0) or 0)
        if active_rows > 0:
            return version_id
        row_counts = CONTAINER.runtime_store.fetchone_dict(
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
