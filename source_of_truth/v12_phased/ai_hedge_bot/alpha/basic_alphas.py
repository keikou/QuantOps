from __future__ import annotations

from ai_hedge_bot.core.types import AlphaResult
from .alpha_registry import ALPHA_REGISTRY


def _direction(score: float, threshold: float = 0.05) -> str:
    if score > threshold:
        return 'long'
    if score < -threshold:
        return 'short'
    return 'neutral'


def _conf(score: float, scale: float = 6.0) -> float:
    return min(abs(score) * scale, 1.0)


def trend_alpha(f: dict[str, float]) -> AlphaResult:
    score = 0.6 * f.get('momentum_4', 0.0) + 0.4 * f.get('trend_strength', 0.0)
    return AlphaResult(ALPHA_REGISTRY['trend_alpha'], _direction(score), float(score), _conf(score, 8), 'trend + momentum')


def mean_reversion_alpha(f: dict[str, float]) -> AlphaResult:
    score = -0.7 * f.get('return_1', 0.0) - 0.3 * f.get('volatility_zscore', 0.0)
    return AlphaResult(ALPHA_REGISTRY['mean_reversion_alpha'], _direction(score), float(score), _conf(score, 8), 'short-term reversal')


def breakout_alpha(f: dict[str, float]) -> AlphaResult:
    score = 0.5 * f.get('momentum_24', 0.0) + 0.5 * f.get('volume_zscore', 0.0)
    return AlphaResult(ALPHA_REGISTRY['breakout_alpha'], _direction(score), float(score), _conf(score, 8), 'breakout + volume')


def funding_squeeze_alpha(f: dict[str, float]) -> AlphaResult:
    score = -(0.8 * f.get('funding_rate', 0.0) + 0.2 * f.get('funding_deviation', 0.0))
    return AlphaResult(ALPHA_REGISTRY['funding_squeeze_alpha'], _direction(score), float(score), _conf(score, 120), 'funding squeeze reversion')


def oi_divergence_alpha(f: dict[str, float]) -> AlphaResult:
    score = 0.7 * f.get('oi_delta', 0.0) - 0.3 * f.get('return_1', 0.0)
    return AlphaResult(ALPHA_REGISTRY['oi_divergence_alpha'], _direction(score), float(score), _conf(score, 2), 'OI divergence')


def liquidation_hunt_alpha(f: dict[str, float]) -> AlphaResult:
    score = -(0.7 * f.get('liquidation_spike', 0.0) + 0.3 * f.get('spread_zscore', 0.0))
    return AlphaResult(ALPHA_REGISTRY['liquidation_hunt_alpha'], _direction(score), float(score), _conf(score, 0.5), 'liquidation sweep reversion')


def orderbook_imbalance_alpha(f: dict[str, float]) -> AlphaResult:
    score = 0.7 * f.get('orderbook_imbalance', 0.0) + 0.3 * f.get('trade_flow_imbalance', 0.0)
    return AlphaResult(ALPHA_REGISTRY['orderbook_imbalance_alpha'], _direction(score), float(score), _conf(score, 3), 'book + trade flow')


def volume_spike_alpha(f: dict[str, float]) -> AlphaResult:
    score = 0.6 * f.get('volume_spike', 0.0) + 0.4 * (f.get('relative_volume', 0.0) - 1.0)
    return AlphaResult(ALPHA_REGISTRY['volume_spike_alpha'], _direction(score), float(score), _conf(score, 1), 'volume spike breakout')


def multi_horizon_momentum_alpha(f: dict[str, float]) -> AlphaResult:
    score = 0.2 * f.get('momentum_1', 0.0) + 0.3 * f.get('momentum_4', 0.0) + 0.5 * f.get('momentum_24', 0.0)
    return AlphaResult(ALPHA_REGISTRY['multi_horizon_momentum_alpha'], _direction(score), float(score), _conf(score, 8), 'multi-horizon momentum')


def short_term_reversal_alpha(f: dict[str, float]) -> AlphaResult:
    score = -0.8 * f.get('return_1', 0.0) - 0.2 * f.get('spread_zscore', 0.0)
    return AlphaResult(ALPHA_REGISTRY['short_term_reversal_alpha'], _direction(score), float(score), _conf(score, 7), 'short-term reversal with spread stress')


def funding_carry_alpha(f: dict[str, float]) -> AlphaResult:
    score = -(0.7 * f.get('funding_rate', 0.0) + 0.3 * f.get('funding_momentum', 0.0))
    return AlphaResult(ALPHA_REGISTRY['funding_carry_alpha'], _direction(score), float(score), _conf(score, 120), 'funding carry')


def aggressive_trade_flow_alpha(f: dict[str, float]) -> AlphaResult:
    score = 0.5 * f.get('trade_flow_imbalance', 0.0) + 0.25 * min(2.0, f.get('aggressive_buy_volume', 0.0) / max(1.0, f.get('aggressive_sell_volume', 1.0))) - 0.25
    return AlphaResult(ALPHA_REGISTRY['aggressive_trade_flow_alpha'], _direction(score), float(score), _conf(score, 1), 'aggressive trade flow')


def liquidation_cascade_alpha(f: dict[str, float]) -> AlphaResult:
    score = 0.7 * f.get('liquidation_spike', 0.0) + 0.3 * abs(f.get('return_4', 0.0))
    signed = score if f.get('return_4', 0.0) > 0 else -score
    return AlphaResult(ALPHA_REGISTRY['liquidation_cascade_alpha'], _direction(signed), float(signed), _conf(score, 0.5), 'liquidation cascade continuation')


def volatility_expansion_alpha(f: dict[str, float]) -> AlphaResult:
    score = 0.6 * f.get('volatility_ratio', 0.0) + 0.2 * f.get('volume_spike', 0.0) + 0.2 * f.get('trend_strength', 0.0) - 0.4
    return AlphaResult(ALPHA_REGISTRY['volatility_expansion_alpha'], _direction(score), float(score), _conf(score, 1), 'volatility expansion breakout')


def vwap_mean_reversion_alpha(f: dict[str, float]) -> AlphaResult:
    score = -0.8 * f.get('price_distance_ma', 0.0) + 0.2 * (f.get('volume_ma_ratio', 1.0) - 1.0)
    return AlphaResult(ALPHA_REGISTRY['vwap_mean_reversion_alpha'], _direction(score), float(score), _conf(score, 8), 'VWAP mean reversion proxy')


def volatility_band_reversion_alpha(f: dict[str, float]) -> AlphaResult:
    denom = max(f.get('atr', 0.0), 1e-9)
    score = -(f.get('price_distance_ma', 0.0) / denom)
    return AlphaResult(ALPHA_REGISTRY['volatility_band_reversion_alpha'], _direction(score), float(score), _conf(score, 0.1), 'volatility band reversion')


def liquidity_sweep_reversion_alpha(f: dict[str, float]) -> AlphaResult:
    score = -0.5 * f.get('liquidation_spike', 0.0) - 0.3 * f.get('spread_zscore', 0.0) + 0.2 * f.get('depth_imbalance', 0.0)
    return AlphaResult(ALPHA_REGISTRY['liquidity_sweep_reversion_alpha'], _direction(score), float(score), _conf(score, 2), 'liquidity sweep reversion')


def funding_mean_reversion_alpha(f: dict[str, float]) -> AlphaResult:
    score = -f.get('funding_deviation', 0.0)
    return AlphaResult(ALPHA_REGISTRY['funding_mean_reversion_alpha'], _direction(score), float(score), _conf(score, 100), 'funding deviation mean reversion')


def oi_momentum_trend_alpha(f: dict[str, float]) -> AlphaResult:
    score = 0.6 * f.get('oi_momentum', 0.0) + 0.4 * f.get('momentum_4', 0.0)
    return AlphaResult(ALPHA_REGISTRY['oi_momentum_trend_alpha'], _direction(score), float(score), _conf(score, 8), 'OI momentum trend')


def cross_asset_relative_momentum_alpha(f: dict[str, float]) -> AlphaResult:
    score = 0.5 * f.get('btc_relative_strength', 0.0) + 0.5 * f.get('eth_relative_strength', 0.0)
    return AlphaResult(ALPHA_REGISTRY['cross_asset_relative_momentum_alpha'], _direction(score), float(score), _conf(score, 8), 'cross-asset relative momentum')


ALPHA_FUNCTIONS = [
    trend_alpha,
    mean_reversion_alpha,
    breakout_alpha,
    funding_squeeze_alpha,
    oi_divergence_alpha,
    liquidation_hunt_alpha,
    orderbook_imbalance_alpha,
    volume_spike_alpha,
    multi_horizon_momentum_alpha,
    short_term_reversal_alpha,
    funding_carry_alpha,
    aggressive_trade_flow_alpha,
    liquidation_cascade_alpha,
    volatility_expansion_alpha,
    vwap_mean_reversion_alpha,
    volatility_band_reversion_alpha,
    liquidity_sweep_reversion_alpha,
    funding_mean_reversion_alpha,
    oi_momentum_trend_alpha,
    cross_asset_relative_momentum_alpha,
]
