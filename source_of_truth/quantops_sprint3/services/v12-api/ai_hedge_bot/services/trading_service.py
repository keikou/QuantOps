from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from typing import Optional

from ai_hedge_bot.core.settings import SETTINGS
from ai_hedge_bot.core.types import Signal
from ai_hedge_bot.core.utils import make_id, utc_now
from ai_hedge_bot.data.collectors.synthetic_market import SyntheticMarketFactory
from ai_hedge_bot.data.collectors.binance_public_client import BinancePublicClient
from ai_hedge_bot.data.storage.jsonl_logger import JsonlLogger
from ai_hedge_bot.features.feature_pipeline import FeaturePipeline
from ai_hedge_bot.regime.regime_classifier import classify_regime
from ai_hedge_bot.alpha.alpha_router import AlphaRouter
from ai_hedge_bot.learning.alpha_learning import AlphaWeightStore
from ai_hedge_bot.portfolio.signal_signature import build_signal_signature
from ai_hedge_bot.portfolio.portfolio_engine import PortfolioEngine
from ai_hedge_bot.portfolio.expected_return_model import ExpectedReturnModel
from ai_hedge_bot.portfolio.optimizer import PortfolioOptimizer
from ai_hedge_bot.portfolio.portfolio_builder import PortfolioBuilder
from ai_hedge_bot.execution.paper_executor import PaperExecutor
from ai_hedge_bot.evaluation.signal_evaluator import SignalEvaluator
from ai_hedge_bot.analytics.analytics_service import AnalyticsSyncService
from ai_hedge_bot.services.execution_intent_service import ExecutionIntentService
from ai_hedge_bot.execution.shadow_engine import ShadowEngine
from ai_hedge_bot.jobs.update_execution_snapshots import run as run_execution_snapshot_job


class TradingService:
    def __init__(self) -> None:
        self.settings = SETTINGS
        self.collector = BinancePublicClient() if self.settings.use_live_market_data else SyntheticMarketFactory(seed=7)
        self.pipeline = FeaturePipeline()
        self.weight_store = AlphaWeightStore(self.settings.weights_path)
        self.router = AlphaRouter(self.weight_store)
        self.portfolio = PortfolioEngine(self.settings.max_gross_exposure, self.settings.max_symbol_weight, self.settings.family_weight_cap)
        self.expected_return_model = ExpectedReturnModel()
        self.optimizer = PortfolioOptimizer()
        self.builder = PortfolioBuilder()
        self.executor = PaperExecutor()
        self.evaluator = SignalEvaluator()
        self.analytics = AnalyticsSyncService(self.settings.db_path, self.settings.log_dir)
        self.signal_logger = JsonlLogger(self.settings.log_dir / 'signals.jsonl')
        self.portfolio_logger = JsonlLogger(self.settings.log_dir / 'portfolio_diagnostics.jsonl')
        self.fill_logger = JsonlLogger(self.settings.log_dir / 'fills.jsonl')
        self.eval_logger = JsonlLogger(self.settings.log_dir / 'evaluations.jsonl')
        self.weight_logger = JsonlLogger(self.settings.log_dir / 'weight_updates.jsonl')
        self.alpha_perf_logger = JsonlLogger(self.settings.log_dir / 'alpha_performance_summary.jsonl')
        self.regime_perf_logger = JsonlLogger(self.settings.log_dir / 'regime_performance_summary.jsonl')
        self.expected_return_logger = JsonlLogger(self.settings.log_dir / 'signal_expected_returns.jsonl')
        self.portfolio_weights_logger = JsonlLogger(self.settings.log_dir / 'portfolio_weights.jsonl')
        self.portfolio_allocations_logger = JsonlLogger(self.settings.log_dir / 'portfolio_allocations.jsonl')
        self.portfolio_risk_logger = JsonlLogger(self.settings.log_dir / 'portfolio_risk_snapshots.jsonl')
        self.runner_state_logger = JsonlLogger(self.settings.log_dir / 'paper_runner_state.jsonl')
        self.execution_intent_service = ExecutionIntentService()
        self.shadow_engine = ShadowEngine()
        self.shadow_decision_logger = JsonlLogger(self.settings.log_dir / 'shadow_decisions.jsonl')
        self.shadow_order_logger = JsonlLogger(self.settings.log_dir / 'shadow_orders.jsonl')
        self.shadow_fill_logger = JsonlLogger(self.settings.log_dir / 'shadow_fills.jsonl')
        self.execution_cost_logger = JsonlLogger(self.settings.log_dir / 'execution_costs.jsonl')
        self.order_event_logger = JsonlLogger(self.settings.log_dir / 'order_events.jsonl')
        self.order_transition_logger = JsonlLogger(self.settings.log_dir / 'order_state_transitions.jsonl')
        self.latency_logger = JsonlLogger(self.settings.log_dir / 'latency_snapshots.jsonl')
        self.shadow_pnl_logger = JsonlLogger(self.settings.log_dir / 'shadow_pnl_snapshots.jsonl')

    def _effective_caps(self, regime: str) -> tuple[float, float]:
        if regime == 'panic':
            return self.settings.panic_gross_exposure, self.settings.panic_symbol_weight
        return self.settings.max_gross_exposure, self.settings.max_symbol_weight

    def _build_signal(self, symbol: str, frame, bundle: dict) -> Optional[Signal]:
        direction = bundle['direction']
        if direction == 'neutral':
            return None
        last = float(frame['close'].iloc[-1])
        atr = float(abs(frame['high'].iloc[-14:] - frame['low'].iloc[-14:]).mean()) if len(frame) >= 14 else float(frame['close'].std())
        stop = last - 1.5 * atr if direction == 'long' else last + 1.5 * atr
        target = last + 2.5 * atr if direction == 'long' else last - 2.5 * atr
        dominant_alpha = bundle['dominant_alpha']
        dominant_meta = next((r.metadata for r in bundle['results'] if r.metadata.alpha_name == dominant_alpha), bundle['results'][0].metadata)
        signature = build_signal_signature(symbol, direction, dominant_meta.alpha_family, round(last, 1))
        return Signal(
            signal_id=make_id('sig', f'{symbol}|{utc_now().isoformat()}|{dominant_alpha}|{direction}'),
            symbol=symbol,
            timestamp=utc_now(),
            side=direction,
            entry=last,
            stop=float(stop),
            target=float(target),
            net_score=float(bundle['net_score']),
            confidence=min(1.0, abs(float(bundle['net_score'])) * 2),
            dominant_alpha=dominant_alpha,
            dominant_alpha_family=dominant_meta.alpha_family,
            signal_horizon=dominant_meta.primary_horizon,
            signal_factor_type=dominant_meta.factor_type,
            signal_signature=signature,
            alpha_results=bundle['results'],
        )

    def run_once(self) -> dict:
        market_frames = {}
        signals: list[Signal] = []
        latest_prices = {}
        alpha_scores = defaultdict(list)
        regime_counts = defaultdict(int)
        symbol_regimes: dict[str, str] = {}
        feature_counts: dict[str, int] = {}

        for symbol in self.settings.symbols:
            frame = self.collector.build_market_frame(symbol=symbol, interval=self.settings.timeframe, limit=200)
            market_frames[symbol] = frame
            latest_prices[symbol] = float(frame['close'].iloc[-1])
            features = self.pipeline.build(frame)
            feature_counts[symbol] = len(features)
            regime = classify_regime(features)
            symbol_regimes[symbol] = regime
            regime_counts[regime] += 1
            bundle = self.router.evaluate(features, regime)
            signal = self._build_signal(symbol, frame, bundle)
            if signal:
                signals.append(signal)
                self.signal_logger.append({'event': 'signal', **asdict(signal), 'regime': regime, 'family_scores': bundle.get('family_scores', {}), 'feature_count': len(features)})

        portfolio_regime = 'panic' if regime_counts.get('panic', 0) >= max(1, len(self.settings.symbols) // 2) else (max(regime_counts.items(), key=lambda x: x[1])[0] if regime_counts else 'range')
        gross_cap, symbol_cap = self._effective_caps(portfolio_regime)
        self.portfolio.max_gross_exposure = gross_cap
        self.portfolio.max_symbol_weight = symbol_cap
        intents, diagnostics = self.portfolio.build(signals, regime=portfolio_regime)
        diagnostics['feature_counts'] = feature_counts
        diagnostics['timestamp'] = utc_now()
        self.portfolio_logger.append(diagnostics)

        expected_returns = [self.expected_return_model.estimate(signal) for signal in signals]
        optimized_weights = self.optimizer.optimize(expected_returns, gross_cap, symbol_cap)
        portfolio_id, portfolio_weights, portfolio_allocations, portfolio_risk = self.builder.build(expected_returns, optimized_weights)
        for item in expected_returns:
            self.expected_return_logger.append({'event': 'expected_return', 'portfolio_id': portfolio_id, **asdict(item)})
        for item in portfolio_weights:
            self.portfolio_weights_logger.append({'event': 'portfolio_weight', **asdict(item)})
        for item in portfolio_allocations:
            self.portfolio_allocations_logger.append({'event': 'portfolio_allocation', **asdict(item)})
        self.portfolio_risk_logger.append({'event': 'portfolio_risk', **asdict(portfolio_risk)})

        fills = self.executor.execute(intents, latest_prices)
        for fill in fills:
            self.fill_logger.append({'event': 'fill', **asdict(fill)})

        positions = [asdict(p) for p in self.executor.mark_to_market(latest_prices)]
        evaluations = []
        alpha_perf = defaultdict(lambda: {'count': 0, 'hit_count': 0, 'sum_1h': 0.0, 'sum_4h': 0.0, 'sum_mfe': 0.0, 'sum_mae': 0.0})
        regime_perf = defaultdict(lambda: {'count': 0, 'hit_count': 0, 'sum_1h': 0.0, 'sum_4h': 0.0})

        for signal in signals:
            evaluation = self.evaluator.evaluate(signal, market_frames[signal.symbol].tail(20).reset_index(drop=True))
            evaluations.append(evaluation)
            self.eval_logger.append({'event': 'evaluation', **asdict(evaluation), 'regime': symbol_regimes.get(signal.symbol, 'range')})
            signal_regime = symbol_regimes.get(signal.symbol, 'range')
            regime_perf[signal_regime]['count'] += 1
            regime_perf[signal_regime]['hit_count'] += int(evaluation.hit)
            regime_perf[signal_regime]['sum_1h'] += evaluation.horizon_1h_return
            regime_perf[signal_regime]['sum_4h'] += evaluation.horizon_4h_return
            for res in signal.alpha_results:
                alpha_scores[res.metadata.alpha_name].append(res.score)
                alpha_perf[res.metadata.alpha_name]['count'] += 1
                alpha_perf[res.metadata.alpha_name]['hit_count'] += int(evaluation.hit)
                alpha_perf[res.metadata.alpha_name]['sum_1h'] += evaluation.horizon_1h_return
                alpha_perf[res.metadata.alpha_name]['sum_4h'] += evaluation.horizon_4h_return
                alpha_perf[res.metadata.alpha_name]['sum_mfe'] += evaluation.mfe
                alpha_perf[res.metadata.alpha_name]['sum_mae'] += evaluation.mae

        alpha_perf_records = []
        for alpha_name, stats in alpha_perf.items():
            count = max(1, stats['count'])
            record = {
                'event': 'alpha_performance',
                'alpha_name': alpha_name,
                'count': stats['count'],
                'hit_rate': round(stats['hit_count'] / count, 6),
                'avg_1h_return': round(stats['sum_1h'] / count, 6),
                'avg_4h_return': round(stats['sum_4h'] / count, 6),
                'avg_mfe': round(stats['sum_mfe'] / count, 6),
                'avg_mae': round(stats['sum_mae'] / count, 6),
                'timestamp': utc_now(),
            }
            alpha_perf_records.append(record)
            self.alpha_perf_logger.append(record)

        regime_perf_records = []
        for regime_name, stats in regime_perf.items():
            count = max(1, stats['count'])
            record = {
                'event': 'regime_performance',
                'regime': regime_name,
                'count': stats['count'],
                'hit_rate': round(stats['hit_count'] / count, 6),
                'avg_1h_return': round(stats['sum_1h'] / count, 6),
                'avg_4h_return': round(stats['sum_4h'] / count, 6),
                'timestamp': utc_now(),
            }
            regime_perf_records.append(record)
            self.regime_perf_logger.append(record)

        averaged_scores = {k: (sum(v) / len(v) if v else 0.0) for k, v in alpha_scores.items()}
        should_update = len(evaluations) >= self.settings.nightly_update_min_evals
        current_weights = self.weight_store.load()
        new_weights = self.weight_store.update_from_scores(averaged_scores) if should_update else current_weights
        self.weight_logger.append({
            'event': 'weights',
            'weights': new_weights,
            'alpha_scores': averaged_scores,
            'timestamp': utc_now(),
            'update_applied': should_update,
            'evaluation_count': len(evaluations),
            'threshold': self.settings.nightly_update_min_evals,
        })
        shadow_intents = self.execution_intent_service.build_intents(portfolio_id, portfolio_weights, portfolio_allocations, latest_prices)
        phase_d = self.shadow_engine.run_cycle(shadow_intents, latest_prices)
        for row in phase_d['shadow_decisions']:
            self.shadow_decision_logger.append(row)
        for row in phase_d['shadow_orders']:
            self.shadow_order_logger.append(row)
        for row in phase_d['shadow_fills']:
            self.shadow_fill_logger.append(row)
        for row in phase_d['execution_costs']:
            self.execution_cost_logger.append(row)
        for row in phase_d['order_events']:
            self.order_event_logger.append(row)
        for row in phase_d['order_state_transitions']:
            self.order_transition_logger.append(row)
        for row in phase_d['latency_snapshots']:
            self.latency_logger.append(row)

        cost_by_order = {row['shadow_order_id']: row for row in phase_d['execution_costs']}
        fill_by_order = {row['shadow_order_id']: row for row in phase_d['shadow_fills']}
        for order_row in phase_d['shadow_orders']:
            fill_row = fill_by_order.get(order_row['shadow_order_id'])
            cost_row = cost_by_order.get(order_row['shadow_order_id'])
            if not fill_row or not cost_row:
                continue
            notional = float(fill_row.get('fill_qty', 0.0) or 0.0) * float(fill_row.get('fill_price', 0.0) or 0.0)
            gross_alpha_pnl_usd = round(notional * 0.0025, 6)
            fee_drag = round(notional * float(fill_row.get('fee_bps', 0.0) or 0.0) / 10000.0, 6)
            slippage_drag = round(notional * abs(float(cost_row.get('slippage_bps', 0.0) or 0.0)) / 10000.0, 6)
            latency_drag = round(notional * abs(float(cost_row.get('latency_cost_bps', 0.0) or 0.0)) / 10000.0, 6)
            net_shadow_pnl_usd = round(gross_alpha_pnl_usd - fee_drag - slippage_drag - latency_drag, 6)
            execution_drag_usd = round(gross_alpha_pnl_usd - net_shadow_pnl_usd, 6)
            self.shadow_pnl_logger.append({
                'event': 'shadow_pnl_snapshot',
                'snapshot_id': make_id('spnl', f"{order_row['shadow_order_id']}|{utc_now().isoformat()}"),
                'portfolio_id': order_row['portfolio_id'],
                'symbol': order_row['symbol'],
                'side': order_row['side'],
                'gross_alpha_pnl_usd': gross_alpha_pnl_usd,
                'net_shadow_pnl_usd': net_shadow_pnl_usd,
                'execution_drag_usd': execution_drag_usd,
                'slippage_drag_usd': slippage_drag,
                'fee_drag_usd': fee_drag,
                'latency_drag_usd': latency_drag,
                'timestamp': utc_now(),
            })

        self.runner_state_logger.append({'event': 'paper_runner_state', 'timestamp': utc_now(), 'status': 'run_once_complete', 'portfolio_id': portfolio_id})
        sync_counts = self.analytics.rebuild()
        sync_counts['execution_snapshots'] = run_execution_snapshot_job(self.analytics.store)
        return {
            'signals': [asdict(s) for s in signals],
            'portfolio_intents': [asdict(i) for i in intents],
            'fills': [asdict(f) for f in fills],
            'positions': positions,
            'evaluations': [asdict(e) for e in evaluations],
            'weights': new_weights,
            'weights_update_applied': should_update,
            'alpha_performance': alpha_perf_records,
            'regime_performance': regime_perf_records,
            'portfolio_regime': portfolio_regime,
            'analytics_sync': sync_counts,
            'phase_c': {
                'portfolio_id': portfolio_id,
                'signal_expected_returns': [asdict(item) for item in expected_returns],
                'portfolio_weights': [asdict(item) for item in portfolio_weights],
                'portfolio_allocations': [asdict(item) for item in portfolio_allocations],
                'portfolio_risk_snapshot': asdict(portfolio_risk),
            },
            'phase_d': {
                'shadow_decision_count': len(phase_d['shadow_decisions']),
                'shadow_order_count': len(phase_d['shadow_orders']),
                'shadow_fill_count': len(phase_d['shadow_fills']),
                'execution_cost_count': len(phase_d['execution_costs']),
                'latest_shadow_orders': phase_d['shadow_orders'],
            },
        }
